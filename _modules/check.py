#!/usr/bin/python
# -*- coding:utf-8 -*-
'''
Create time:    2016-01-08
author:         fire
'''

# Import python libs
import os
import logging

# Import salt libs
import salt.utils
import salt.client
import salt.fileclient
#from salt.modules.cp import hash_file

#caller = salt.client.Caller()
log = logging.getLogger(__name__)

def _mk_client():
    '''
    Create a file client and add it to the context.
    '''
    if 'cp.fileclient' not in __context__:
        __context__['cp.fileclient'] = \
                salt.fileclient.get_file_client(__opts__)

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

def file(saltpath,dest):

    '''
    Used to check the MD5 value for two files which are a file on the salt master and a local file 

    CLI Example:

    .. code-block:: bash

        salt '*' check.file salt://path/to/file /minion/dest

    '''
    if os.path.exists(dest):
        hash_dest = hash_file(dest)
	hash_salt = hash_file(saltpath)
        if hash_dest == hash_salt:
            return True
	else:
	    return False

    else:
        log.error("local file is not exists,dest=%s" %dest )
        return False

