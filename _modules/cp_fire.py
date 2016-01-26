# -*- coding: utf-8 -*-
'''
Minion side functions for salt-cp
'''
from __future__ import absolute_import

# Import python libs
import os
import sys
import logging
import fnmatch
import hashlib

# Import salt libs
import salt.minion
import salt.fileclient
import salt.utils
import salt.crypt
import salt.transport
from salt.exceptions import CommandExecutionError

log = logging.getLogger(__name__)

def _auth():
    '''
    Return the auth object
    '''
    if 'auth' not in __context__:
        __context__['auth'] = salt.crypt.SAuth(__opts__)
    return __context__['auth']

def _mk_client():
    '''
    Create a file client and add it to the context.
    '''
    if 'cp.fileclient' not in __context__:
        __context__['cp.fileclient'] = \
                salt.fileclient.get_file_client(__opts__)

def _render_filenames(path, dest, saltenv, template):
    '''
    Process markup in the :param:`path` and :param:`dest` variables (NOT the
    files under the paths they ultimately point to) according to the markup
    format provided by :param:`template`.
    '''
    if not template:
        return (path, dest)

    # render the path as a template using path_template_engine as the engine
    if template not in salt.utils.templates.TEMPLATE_REGISTRY:
        raise CommandExecutionError(
            'Attempted to render file paths with unavailable engine '
            '{0}'.format(template)
        )

    kwargs = {}
    kwargs['salt'] = __salt__
    kwargs['pillar'] = __pillar__
    kwargs['grains'] = __grains__
    kwargs['opts'] = __opts__
    kwargs['saltenv'] = saltenv

    def _render(contents):
        '''
        Render :param:`contents` into a literal pathname by writing it to a
        temp file, rendering that file, and returning the result.
        '''
        # write out path to temp file
        tmp_path_fn = salt.utils.mkstemp()
        with salt.utils.fopen(tmp_path_fn, 'w+') as fp_:
            fp_.write(contents)
        data = salt.utils.templates.TEMPLATE_REGISTRY[template](
            tmp_path_fn,
            to_str=True,
            **kwargs
        )
        salt.utils.safe_rm(tmp_path_fn)
        if not data['result']:
            # Failed to render the template
            raise CommandExecutionError(
                'Failed to render file path with error: {0}'.format(
                    data['data']
                )
            )
        else:
            return data['data']

    path = _render(path)
    dest = _render(dest)
    return (path, dest)

def hash_file(path, saltenv='base', env=None):
    '''
    Return the hash of a file, to get the hash of a file on the
    salt master file server prepend the path with salt://<file on server>
    otherwise, prepend the file with / for a local file.

    CLI Example:

    .. code-block:: bash

        salt '*' cp.hash_file salt://path/to/file
    '''
    if env is not None:
        salt.utils.warn_until(
            'Boron',
            'Passing a salt environment should be done using \'saltenv\' '
            'not \'env\'. This functionality will be removed in Salt Boron.'
        )
        # Backwards compatibility
        saltenv = env

    _mk_client()
    return __context__['cp.fileclient'].hash_file(path, saltenv)

def getFileMd5(filename):
    if not os.path.isfile(filename):
        return
    myhash = hashlib.md5()
    f = file(filename,'rb')
    while True:
        b = f.read(8096)
        if not b :
            break
        myhash.update(b)
    f.close()
    return myhash.hexdigest()

def get_dir(
            path, 
	    dest, 
	    saltenv='base', 
	    template=None, 
	    gzip=None, 
	    env=None
	    ):
    '''
    Used to recursively copy a directory from the salt master

    CLI Example:

    .. code-block:: bash

        salt '*' cp_mb.get_dir salt://path/to/dir/ /minion/dest

    get_dir supports the same template and gzip arguments as get_file.
    '''
    if env is not None:
        salt.utils.warn_until(
            'Boron',
            'Passing a salt environment should be done using \'saltenv\' '
            'not \'env\'. This functionality will be removed in Salt Boron.'
        )
        # Backwards compatibility
        saltenv = env

    (path, dest) = _render_filenames(path, dest, saltenv, template)

    _mk_client()
    files = __context__['cp.fileclient'].get_dir(path, dest, saltenv, gzip)
    file_md5 = []
    for fl in files:
        file_md5.append((fl, getFileMd5(fl)))
    return file_md5

def get_file(path,
             dest,
             saltenv='base',
             makedirs=False,
             template=None,
             gzip=None,
             env=None):
    '''
    Used to get a single file from the salt master

    CLI Example:

    .. code-block:: bash

        salt '*' cp.get_file salt://path/to/file /minion/dest

    Template rendering can be enabled on both the source and destination file
    names like so:

    .. code-block:: bash

        salt '*' cp.get_file "salt://{{grains.os}}/vimrc" /etc/vimrc template=jinja

    This example would instruct all Salt minions to download the vimrc from a
    directory with the same name as their os grain and copy it to /etc/vimrc

    For larger files, the cp.get_file module also supports gzip compression.
    Because gzip is CPU-intensive, this should only be used in scenarios where
    the compression ratio is very high (e.g. pretty-printed JSON or YAML
    files).

    Use the *gzip* named argument to enable it.  Valid values are 1..9, where 1
    is the lightest compression and 9 the heaviest.  1 uses the least CPU on
    the master (and minion), 9 uses the most.
    '''
    if env is not None:
        salt.utils.warn_until(
            'Boron',
            'Passing a salt environment should be done using \'saltenv\' '
            'not \'env\'. This functionality will be removed in Salt Boron.'
        )
        # Backwards compatibility
        saltenv = env

    (path, dest) = _render_filenames(path, dest, saltenv, template)

    if not hash_file(path, saltenv):
        return ''
    else:
        _mk_client()
        file =  __context__['cp.fileclient'].get_file(
                path,
                dest,
                makedirs,
                saltenv,
                gzip)
        file_md5 = getFileMd5(file)
        return file,file_md5

def push(path, keep_symlinks=False):
    '''
    Push a file from the minion up to the master, the file will be saved to
    the salt master in the master's minion files cachedir
    (defaults to ``/var/cache/salt/master/minions/minion-id/files``)

    Since this feature allows a minion to push a file up to the master server
    it is disabled by default for security purposes. To enable, set
    ``file_recv`` to ``True`` in the master configuration file, and restart the
    master.

    keep_symlinks
        Keep the path value without resolving its canonical form

    CLI Example:

    .. code-block:: bash

        salt '*' cp.push /etc/fstab
        salt '*' cp.push /etc/system-release keep_symlinks=True
    '''
    log.debug('Trying to copy {0!r} to master'.format(path))
    if '../' in path or not os.path.isabs(path):
        log.debug('Path must be absolute, returning False')
        return False
    if not keep_symlinks:
        path = os.path.realpath(path)
    if not os.path.isfile(path):
        log.debug('Path failed os.path.isfile check, returning False')
        return False
    auth = _auth()

    load = {'cmd': '_file_recv',
            'id': __opts__['id'],
            'path': path.lstrip(os.sep),
            'tok': auth.gen_token('salt')}
    channel = salt.transport.Channel.factory(__opts__)
    with salt.utils.fopen(path, 'rb') as fp_:
        while True:
            load['loc'] = fp_.tell()
            load['data'] = fp_.read(__opts__['file_buffer_size'])
            '''
            if not load['data']:
                return True
            '''
            ret = channel.send(load)
            if not ret:
                log.error('cp.push Failed transfer failed. Ensure master has '
                '\'file_recv\' set to \'True\' and that the file is not '
                'larger than the \'file_recv_size_max\' setting on the master.')
                return ret
            else:
                return path,getFileMd5(path)

def push_dir(path, glob=None):
    '''
    Push a directory from the minion up to the master, the files will be saved
    to the salt master in the master's minion files cachedir (defaults to
    ``/var/cache/salt/master/minions/minion-id/files``).  It also has a glob
    for matching specific files using globbing.

    .. versionadded:: 2014.7.0

    Since this feature allows a minion to push files up to the master server it
    is disabled by default for security purposes. To enable, set ``file_recv``
    to ``True`` in the master configuration file, and restart the master.

    CLI Example:

    .. code-block:: bash

        salt '*' cp.push /usr/lib/mysql
        salt '*' cp.push_dir /etc/modprobe.d/ glob='*.conf'
    '''
    if '../' in path or not os.path.isabs(path):
        return False
    path = os.path.realpath(path)
    if os.path.isfile(path):
        return push(path)
    else:
        filelist = []
        ret = []
        for root, dirs, files in os.walk(path):
            filelist += [os.path.join(root, tmpfile) for tmpfile in files]
        if glob is not None:
            filelist = [fi for fi in filelist if fnmatch.fnmatch(fi, glob)]
        for tmpfile in filelist:
            log.error(tmpfile)
            ret.append(push(tmpfile))
        return ret
	