# -*- coding: utf-8 -*-

# multimail - inviatore di email (mmutils.py module)

# Copyright (C) 2009  Marco Chieppa

# mmutils.py is part of multimail.
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not see <http://www.gnu.org/licenses/>


from __future__ import with_statement
import os
import time
import shlex
import subprocess as subp
import os.path as osp
import zipfile
import tarfile
import tempfile
import platform
import ConfigParser


py_version = ''.join(platform.python_version_tuple()[:2])
if py_version < '26':
    # from the python doc
    from itertools import chain, repeat, izip
    def izip_longest(*args, **kwds):
        fillvalue = kwds.get('fillvalue')
        def sentinel(counter = ([fillvalue]*(len(args)-1)).pop):
            yield counter()
        fillers = repeat(fillvalue)
        iters = [chain(it, sentinel(), fillers) for it in args]
        try:
            for tup in izip(*iters):
                yield tup
        except IndexError:
            pass
else:
    from itertools import izip_longest
if py_version < '27':
    from contextlib import closing
else:
    class closing(object):
        def __init__(self, target):
            self.target = target
        def __enter__(self):
            return self.target
        def __exit__(self, exc_type, exc_value, traceback):
            self.target.close()

def _walk(path):
    """A walk for zip archives."""
    for base_dir, sub_dirs, files in os.walk(path):
        for d in sub_dirs:
            yield osp.join(base_dir, d)
        for f in files:
            yield osp.join(base_dir, f)


def create_archive(paths, arch_type, arch_path=None):
    """
    Create an archive in *arch_type* format with the provided
    *paths*. Use tempfile if *arch_path* is not given,
    otherwise *arch_path* is used and must be a valid path name.
    Return the path to the archive (which is *arch_path* if
    provided) or None if the archive type is not a supported one.
    """
    atype = arch_type.lower()
    if not arch_path:
        with tempfile.NamedTemporaryFile() as f:
            c = '.tar' if atype in ('gz', 'bz2') else ''
            arch_path = f.name + c + '.' + atype
    if atype == 'zip':
        with closing(zipfile.ZipFile(arch_path, 'w')) as archive:
            for path in paths:
                if osp.isfile(path):
                    archive.write(path, osp.basename(path))
                if osp.isdir(path):
                    path = path.rstrip(os.sep)
                    spath = path + os.sep
                    _basename = osp.basename(path)
                    archive.write(path, _basename)
                    for p in _walk(path):
                        if osp.isdir(p):
                            archive.write(p, osp.join(
                                _basename, osp.basename(p.rstrip(os.sep))))
                        else:
                            archive.write(p, osp.join(
                                _basename, spath.join(p.split(spath)[1:])))
    elif atype in ('tar', 'gz', 'bz2'):
        aop = {'tar':'w:', 'gz':'w:gz', 'bz2':'w:bz2'}
        with closing(tarfile.open(arch_path, aop[atype])) as archive:
            for path in paths:
                archive.add(path, osp.basename(path.rstrip(os.sep)))
    else:
        return None
    return arch_path

#gpg_key_id = '79631020'
#gpg_exe = 'gpg'
#'--default-key'
#'--clearsign' # .asc
#'_output': '--output %s'
#--detach-sig  #.sig


def build_gpg_cmd(exe, key, infile, outfile, detached):
    s_type = '--clearsign' if not detached else '--detach-sig'
    cmdline = "%s --default-key %s --output %s %s %s" % (
        exe, key, outfile, s_type, infile)
    return shlex.split(cmdline)  #ValueError: (no closing quotation)

def do_sign(cmdline):
    try:
        subp.check_call(cmdline)
        return True
    except subp.CalledProcessError:
        return False
    
def gpg_sign(gpg_exe, gpg_key_id, text, detach):
    with tempfile.NamedTemporaryFile() as fin:
        to_sign = fin.name
    with tempfile.NamedTemporaryFile() as fout:
        signed = fout.name
    with open(to_sign, 'w') as f:
        f.write(text)
    if not do_sign(build_gpg_cmd(gpg_exe, gpg_key_id, to_sign, signed, detach)):
        os.remove(to_sign)
        raise ValueError('Unable to sign')
    os.remove(to_sign)
    return signed

def mail_format_time():
    """
    Return the actual time and date as a string in a
    format compliant with the RFC822 specification.
    """
    gtime = time.gmtime()
    ltime = time.localtime()
    _delta = abs(ltime.tm_hour - gtime.tm_hour)
    delta = 0 if not _delta else 24 % _delta
    diff = "%s%02d00" % ('-' if ltime < gtime else '+', delta)
    return "%s %s" % (time.strftime(
        "%a, %d %b %Y %H:%M:%S", time.localtime()), diff)


def read_config(file):
    """Return a configparser object from *file*."""
    config = ConfigParser.ConfigParser()
    config.readfp(open(file))
    return config

def fake_config(section):
    opts = ["host", "port", "ssl_port", "secure_conn",
            "timeout", "debug_mode", "delay", "editor",
            "sender", "login", "password", "text_type",]
    config = ConfigParser.ConfigParser()
    if section != 'DEFAULT':
        config.add_section(section)
    for opt in opts:
        config.set(section, opt, '')
    return config
