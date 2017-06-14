#!/usr/bin/env python

import os
import sys
import subprocess as sp
import json
import re


HEADERS = ['.h', '.hpp']
SOURCES = ['.cpp', '.cxx']
CPP_FILES = HEADERS + SOURCES
PACKAGE = 'package.json'

RE_NAMESPACE = re.compile(r'namespace\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*{')


def main():
    """Run npm command and post-process newly-installed C++ files.

    :return: 0 on success, error code on failure.
    """

    cmd = ['npm'] + sys.argv[1:]
    child = sp.Popen(cmd, stdout=sp.PIPE)
    _x = child.communicate()[0]
    if child.returncode:
        print 'Failed to run npm command %s' % ' '.join(cmd)
        return -1
    npm_command = sys.argv[1]
    if npm_command in ('install', 'upgrade'):
        return post_process()
    else:
        print 'Command finished successfully:\n\t%s' % ' '.join(cmd)
        print 'Since it was not "install" or "upgrade", not post-processing C++ dependencies'
        return 0


def post_process():
    """Go into node_modules and recursively fix all C++ namespaces.

    The goal is to avoid linker errors caused by multiple versions of the same C++ package installed through
    different intermediate dependencies.

    :return: 0 on success, error code on failure.
    """

    for dirpath, dirnames, filenames in os.walk('node_modules'):
        print 'Walking %s: %s, %s, %s' % ('node_modules', dirpath, dirnames, filenames)
        if PACKAGE in filenames:
            version, pkgname = get_version(dirpath)
            print 'working with %s, version: %s' % (dirpath, version)
        for fname in filenames:
            is_candidate = False
            for ext in CPP_FILES:
                if fname.lower().endswith(ext):
                    is_candidate = True
                    break
            if is_candidate:
                process_file(os.path.join(dirpath, fname), version, pkgname)


def get_version(dirpath):
    fname = os.path.join(dirpath, PACKAGE)
    package = json.load(open(fname))
    return 'v' + package['version'].replace('.', '_'), re.sub(r'[^a-zA-Z0-9_]', '_', package['name'])


def process_file(fpath, version, pkgname):
    print 'processing %s @ %s' % (fpath, version)
    suffix = '_%s' % version
    text = open(fpath).read()
    match = RE_NAMESPACE.search(text)
    if match:
        ns = match.group(1)
        print 'found namespace: %s' % ns
        if ns.endswith(suffix):
            print 'Looks like %s has already been processed' % fpath
            return
        print 'Found namespace %s in %s, decorating with %s' % (ns, fpath, suffix)
        ns2 = ns + suffix
        text2 = RE_NAMESPACE.sub(r'namespace \1%s {' % suffix, text)
        is_header = False
        for h in HEADERS:
            if fpath.lower().endswith(h):
                is_header = True
                break
        if is_header:
            define_name = '_'.join(('DD_NS_DECORATION', pkgname.replace('.', '_'), ns)).upper()
            if define_name in text:
                print 'Something is wrong: "%s" is already in the file' % define_name
                return
            last_undef_pos = text2.rfind('#endif')
            text2 = '\n'.join((text2[:last_undef_pos],
                               '#ifndef %s\n#define %s\nnamespace %s = %s;\n#endif\n\n' % (define_name, define_name, ns, ns2),
                              text2[last_undef_pos:]))
        print 'rewriting %s' % fpath
        open(fpath, 'w').write(text2)


if __name__ == '__main__':
    sys.exit(main())
