# tool that builds an application to be run in container

import os
import sys
import tempfile
import configparser

config = configparser.ConfigParser()

build_top = os.environ.get("BUILD_TOP")
sys.path.append(f"{build_top}/build/make/core")
from envsetup import *


container_builder_version = '1.0'

container_install_dir = 'opt/run/containers/'

compatable_container_versions= {
    '1.0',
}



container_layout = {
    'lib',
    'lib64',
    'bin',
    'etc',
    'xbin',
}

def generate_tmpdir():
    container_build_dir = (f'{target_product_out}/obj/container/{target_build_variant}/build_tmp')
    os.makedirs(container_build_dir, exist_ok=True)
    # generate a roaming tmpdir for the container
    # __TMP__?/remember to clean up
    tmpdir = tempfile.mkdtemp(dir=container_build_dir)
    os.makedirs(tmpdir, exist_ok=True)
    f = open(file=f'{tmpdir}/container.conf', mode='w')
    f.write(f'container_version={container_builder_version}')
    f.write(f'container_build_variant={target_build_variant}')
    for i in container_layout:
        os.makedirs(f'{tmpdir}/{i}', exist_ok=True)


def check_container_version():
    config.read(f'{container_source_dir}/container.ini')
    container_version = config.get('container', 'version')






def build_container_module():
    generate_tmpdir()


def create_module_image():
    shutil.copyfile()


generate_tmpdir()