#!/usr/bin/env python
#
# fibfs.py - Fake iOS Backup Filesystem
#
# 2017.03.01 darell tan
#

import fuse
import os
import sys
import stat
import errno
import shutil
import tempfile

fuse.fuse_python_api = (0, 2)
fuse.feature_assert('stateful_files', 'has_fsinit')


def join_path(obj, *parts):
	p1 = parts[0]
	if p1.startswith('/'):
		p1 = p1[1:]
	return os.path.join(obj.backing_dir, p1, *parts[1:])


class FibFs(fuse.Fuse):
	def __init__(self, *args, **kwargs):
		fuse.Fuse.__init__(self, *args, **kwargs)

		self.file_class = self.fileObjClass()
		self.rm_backing_dir = False
		self.multithreaded = False

		self.parser.add_option('--backing-dir', metavar='DIR', default=None, dest='backing_dir', 
				help='specifies the directory where data is stored')
		self.parser.add_option('--freespace', metavar='SIZE', default=128, type='int', dest='freespace', 
				help='amount of free disk space (in GBs) to report [default: %default]')

	def fsinit(self):
		options, args = self.cmdline
		self.backing_dir = options.backing_dir
		self.freespace = options.freespace * 1024 ** 3
		if self.backing_dir is None:
			self.rm_backing_dir = True
			self.backing_dir = tempfile.mkdtemp(prefix='fibfs.')

	def fsdestroy(self):
		if self.rm_backing_dir:
			shutil.rmtree(self.backing_dir)

	def _rpath(self, *parts):
		return join_path(self, *parts)

	def keep_file(self, path):
		name = os.path.basename(path)
		if name.startswith('Manifest') or name.endswith('.plist'):
			return True
		return False

	def readdir(self, path, offset):
		rpath = self._rpath(path)
		entries = ['.', '..'] + os.listdir(rpath)
		for e in entries:
			typ = 0
			if os.path.isdir(os.path.join(rpath, e)):
				typ |= stat.S_IFDIR
			else:
				typ |= stat.S_IFREG

			yield fuse.Direntry(name=e, type=typ)

	def truncate(self, path, size):
		f = self.file_class(path, os.O_WRONLY | os.O_TRUNC)
		f.ftruncate(size)
		f.release(None)

	def statfs(self):
		st = os.statvfs(self.backing_dir)
		st_dict = {}
		for k in ('bsize', 'frsize', 'blocks', 'bfree', 'bavail', 'files', 'ffree', 'favail', 'namemax'):
			k = 'f_' + k
			st_dict[k] = getattr(st, k)

		freeblocks = self.freespace / st_dict['f_bsize']
		st_dict['f_bfree']  += freeblocks
		st_dict['f_bavail'] += freeblocks
		st_dict['f_blocks'] += freeblocks

		return fuse.StatVfs(**st_dict)

	def getattr(self, path): return os.lstat(self._rpath(path))

	###

	def mkdir(self, path, mode): return os.mkdir(self._rpath(path), mode)

	def rmdir(self, path): return os.rmdir(self._rpath(path))

	def link(self, path1, path2): return os.link(self._rpath(path1), self._rpath(path2))

	def unlink(self, path): return os.unlink(self._rpath(path))

	def chmod(self, path, mode): return os.chmod(self._rpath(path), mode)

	def chown(self, path, uid, gid): return os.chown(self._rpath(path), uid, gid)

	def utime(self, path, times): return os.utime(self._rpath(path), times)

	def readlink(self, path): return os.readlink(self._rpath(path))

	def rename(self, path1, path2): return os.rename(self._rpath(path1), self._rpath(path2))

	def access(self, path, mode): return -errno.EACCESS if not os.access(self._rpath(path), mode) else 0


	def fileObjClass(fs):
		class FileObj(object):
			def _rpath(self, *parts):
				return join_path(fs, *parts)

			def __init__(self, path, flags, *mode):
				rpath = self._rpath(path)
				self.direct_io = False
				self.keep_cache = False

				self.is_dummy_file = not fs.keep_file(path)
				if self.is_dummy_file:
					flags |= os.O_TRUNC

				self.f = os.open(rpath, flags, *mode)
				self.max_size = os.fstat(self.f).st_size

			def seek(self, pos):
				os.lseek(self.f, pos, os.SEEK_SET)

			def read(self, length, offset):
				self.seek(offset)
				return os.read(self.f, length)

			def write(self, buf, offset):
				self.seek(offset)
				self.max_size = max(self.max_size, offset + len(buf))
				if self.is_dummy_file:
					return len(buf)
				return os.write(self.f, buf)

			def ftruncate(self, size):
				self.max_size = size
				return os.ftruncate(self.f, size)

			def fgetattr(self):
				return os.fstat(self.f)

			def release(self, flags):
				if self.is_dummy_file and self.max_size > 0:
					self.seek(self.max_size - 1)
					os.write(self.f, '\0')
				os.close(self.f)
				self.f = None

		return FileObj


if __name__ == '__main__':
	fs = FibFs()
	try:
		opts = fs.parse(errex=1)

		# if mountpoint was not specified, show help
		if fs.fuse_args.mount_expected() and opts.mountpoint is None:
			fs.parse(['-h'])

		opts2 = fs.cmdline[0]
		if opts2.backing_dir is not None and not os.path.isdir(opts2.backing_dir):
			raise ValueError('backing dir %r is not a dir' % opts2.backing_dir)

		fs.main()
	except:
		etyp, ev = sys.exc_info()[:2]
		print('error: %s' % ev)

