Fake iOS Backup Filesystem (fibfs)
====================================

A FUSE-based filesystem that is to be used with `idevicebackup` for iOS backups.
The filesystem discards the actual backup data, but retains metadata such as 
plists and `Manifest.*` files.

This filesystem is helpful if you only need to get data that is contained
within the metadata files.
By discarding all the backup data, a backup only consumes less than 10 MB of 
actual disk space. It also reduces disk I/O, which helps to speed up the backup process.

It works by layering on top of a *backing directory*.
For files whose contents are to be discarded, it writes only a single byte at the end of the file, 
but for files which need to be preserved, it writes the contents in its entirety.
For efficient storage, it uses *sparse files* in the backing directory.
This way, all the file metadata (such as size, last modified time, etc) is preserved, 
but the backup data files will contain all zero bytes and take up a minimal amount of space.


Usage
======

You will need Python & FUSE (and Python bindings for FUSE). 
On Fedora/RHEL, you can install it like so:

    yum install fuse-python

The simplest usage is to specify a directory to mount the filesystem:

    fibfs.py <mountpoint>

A backing directory will be automatically created in `/tmp`, and when the
filesystem is unmounted, this directory will be destroyed. If you need to save
any data, do it before you unmount the filesystem.

If you wish to retain the files or you already have files from a previous
backup session, you can manually specify a backing directory with
`--backing-dir`. This directory will NOT be removed after an unmount.


License
========

**fibfs is licensed under the 3-clause ("modified") BSD License.**

Copyright (C) 2017 Darell Tan

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions
are met:

1. Redistributions of source code must retain the above copyright
   notice, this list of conditions and the following disclaimer.
2. Redistributions in binary form must reproduce the above copyright
   notice, this list of conditions and the following disclaimer in the
   documentation and/or other materials provided with the distribution.
3. The name of the author may not be used to endorse or promote products
   derived from this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE AUTHOR "AS IS" AND ANY EXPRESS OR
IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES
OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.
IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY DIRECT, INDIRECT,
INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT
NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF
THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

