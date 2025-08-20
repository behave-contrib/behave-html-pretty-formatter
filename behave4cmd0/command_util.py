"""
Provides some command utility functions.
"""

import os.path
import shutil
import sys
import tempfile
import time
from fnmatch import fnmatch

from . import pathutil
from .__setup import TOP, TOPA

WORKDIR = os.path.join(TOP, "__WORKDIR__")


def workdir_save_coverage_files(workdir, destdir=None):
    assert os.path.isdir(workdir)
    if not destdir:
        destdir = TOPA
    if os.path.abspath(workdir) == os.path.abspath(destdir):
        return  # -- SKIP: Source directory is destination directory (SAME).

    for fname in os.listdir(workdir):
        if fnmatch(fname, ".coverage.*"):
            sourcename = os.path.join(workdir, fname)
            shutil.move(sourcename, destdir)


def ensure_context_attribute_exists(context, name, default_value=None):
    """
    Ensure a behave resource exists as attribute in the behave context.
    If this is not the case, the attribute is created by using the default_value.
    """
    if not hasattr(context, name):
        setattr(context, name, default_value)


def ensure_workdir_exists(context):
    """
    Ensures that the work directory exists.
    In addition, the location of the workdir is stored as attribute in
    the context object.
    """
    ensure_context_attribute_exists(context, "workdir", None)
    if not context.workdir:
        context.workdir = os.path.abspath(WORKDIR)
    pathutil.ensure_directory_exists(context.workdir)


def ensure_workdir_not_exists(context):
    """Ensures that the work directory does not exist."""
    ensure_context_attribute_exists(context, "workdir", None)
    if context.workdir:
        orig_dirname = real_dirname = context.workdir
        context.workdir = None
        if os.path.exists(real_dirname):
            renamed_dirname = tempfile.mktemp(
                prefix=os.path.basename(real_dirname),
                suffix="_DEAD",
                dir=os.path.dirname(real_dirname) or ".",
            )
            os.rename(real_dirname, renamed_dirname)
            real_dirname = renamed_dirname
        max_iterations = 2
        if sys.platform.startswith("win"):
            max_iterations = 15

        for iteration in range(max_iterations):
            if not os.path.exists(real_dirname):
                if iteration > 1:
                    print("REMOVE-WORKDIR after %s iterations" % (iteration + 1))
                break
            shutil.rmtree(real_dirname, ignore_errors=True)
            time.sleep(0.5)
        assert not os.path.isdir(real_dirname), "ENSURE not-isa dir: %s" % real_dirname
        assert not os.path.exists(real_dirname), (
            "ENSURE dir not-exists: %s" % real_dirname
        )
        assert not os.path.isdir(orig_dirname), "ENSURE not-isa dir: %s" % orig_dirname
