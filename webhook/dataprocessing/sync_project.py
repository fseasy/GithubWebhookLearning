#/usr/bin/env python
#coding=utf-8

import argparse
import sys
import os
import json
import logging
import traceback

logging.basicConfig(level=logging.INFO ,
                    format="%(asctime)s %(levelname)% %(funcName)s[%(lineno)d] : %(message)s")

def enum(**enums) :
    return type('Enum',(),enums)

DepType = enum(FILE="file",DIR="dir",CMAKELISTS="cmakelists")
DepChangeState = enum(MODIFIED="MODIFIED",UN_CHANGE="UN_CHANGE" , ADD="ADD" , SYNC="SYNC")

def get_segmentor_dependency(dep_f) :
    '''
    return > dep_s : [
        {
            type : ["file"|"dir"|"cmakelists"] 
            path : ["path/to/obj",...] 
            change_state : ["MODIFIED"|"UN_CHANGE"|"ADD"|"SYNC"]
        }
    ]
    '''
    dep_s = {}
    all_dep_s = json.load(dep_f , encoding="utf-8")
    try :
        dep_s = all_dep_s["subproject"]["segmentor"]
    except KeyError , e :
        traceback.print_exc()
        exit(1)
    return dep_s

def add_directory_hierarchy(vdh , dep_path , is_dir=False) :
    part_list = []
    while True :
        head , tail = os.path.split(dep_path)
        part_list.append(tail)
        if head == '' :
            break
    parent_dir = vdh
    for i in range(len(part_list)-1 , 0 , -1) :
        cur_dir_name = part_list[i]
        if cur_dir_name not in parent_dir :
            parent_dir[cur_dir_name] = {}
        parent_dir = parent_dir[cur_dir_name]
    basename = part_list[0]
    if not is_dir :
        parent_dir[basename] = None
    else :
        parent_dir[basename] = {}
def rm_file_or_dir(path) :
    if not os.path.exists(path) :
        logging.info("file to be removed is not exists : %s" %(path))
        return
    if os.isdir(path) :
        shutil.rmtree(path)
    else :
        os.remove(path)

def copy_file_or_dir(src_path , dst_path , is_dir) :
    '''
    copy src to dst . 
    Attention ! we'll first check if dst path is exists && is dir , if so , we'll firstly remove it !  
    '''
    if not os.path.exists(src_path) :
        logging.warning("source path : %s is not exists . Copy Aborted !" %(src_path))
        return False
    physically_is_dir == os.path.isdir(src_path)
    if physically_is_dir != is_dir : 
        logging.warning("path : %s is actually %s , dependency file config wrong" %(src_path , "directory" if physically_is_dir else "file"))
    try :
        if physically_is_dir :
            if os.path.exists(dst_path) :
                shutil.rmtree(dst_path)
            shutil.copytree(src_path , dst_path) # ensure dst_path do not exists
        else :
            head_path = os.path.split(dst_path)[0]
            if not os.path.exists(head_path) :
                os.makedirs(head_path)
            shutil.copy2(src_path , dst_path) # ensure dst_path's dir be exists
    except Exception , e :
        logging.warning("copy process error. detail info : %s" %(e))
        return False
    return True

def sync_file_or_dir(src_path , dst_path , path_type , sync_strategy) :
    copy_ret = True
    if sync_strategy == DepChangeState.NO_CHANGE :
        if not os.path.exists(dst_path) :
            copy_ret = copy_file_or_dir(src_path , dst_path , path_type==DepType.DIR)
        else :
            copy_ret = False
    else :
        copy_ret = copy_file_or_dir(src_path , dst_path , path_type==DepType.DIR)
    return copy_ret

def copy_needed_file_and_build_new_virtual_directory_hierarchy(src_root_path , dst_root_path , dep_s , vdh) :
    copy_counter = 0
    for dep in dep_s :
        dep_type = dep['type']
        dep_paths = dep['path'] if type(dep['path']) == list else [dep['path']]
        dep_change_state = dep['change_state']
        for dep_path in dep_paths :
            src_path = os.path.join(src_root_path , dep_path)
            dst_path = os.path.join(dst_root_path , dep_path)
        
            add_directory_hierarchy(vdh , dep_path , dep_type==DepType.DIR )
            sync_state = sync_file_or_dir(src_path , dst_path ,  dep_type , dep_change_state) 
            if sycn_state :
                copy_counter += 1
    print "copy result : %d/%d copied" %(copy_counter,len(dep_s))

def build_keep_stable_virtual_directory_hierarchy(keep_stable_describe_f ) :
    vdh = {}
    if keep_stable_describe_f == None :
        return vdh
    for line in keep_stable_describe_f :
        path = line.strip()
        add_directory_hierarchy(vdh , path , os.path.isdir(path) )
    return vdh

def rm_redundant_files_and_dirs(dst_root_path , new_vdh , keep_stable_vdh) :
    if dst_root_path == "" or not os.path.isdir(dst_root_path) : 
        return
    if new_vdh is None or len(new_vdh) == 0 :
        return
    names = os.lsdir(dst_root_path)
    for fname in names :
        fpath = os.path.join(dst_root_path , fname)
        if fname in new_vdh :
            ## recursive call to clear redundant in sub dir
            next_dst_root_path = fpath
            next_new_vdh = new_vdh[fname]
            next_keep_stable_vdh = keep_stable_vdh.get(fname , {})
            rm_redundant_files_and_dirs(next_dst_root_path , next_new_vdh , next_keep_stable_vdh)
        else :
            if fname not in keep_stable_vdh :
                rm_file_or_dir(fpath)

def main(dep_f , keep_stable_describe_f ) :
    dep_s = get_segmentor_dependency(dep_f)
    print dep_s

    keep_stable_vdh = build_keep_stable_virtual_directory_hierarchy(keep_stable_describe_f)
    print keep_stable_vdh


if __name__ == "__main__" :
    argp = argparse.ArgumentParser(description="keep two dirs synchronization")
    argp.add_argument("-d" , "--dependency_file" , help="the file that describe the dependency of the dest dir , from the src dir . JSON formated. detail info please see the example json file.",required=True , type=argparse.FileType('r'))
    argp.add_argument('-k' , "--keep_stable_file" , help="the file that describe which files and dirs of dest dir shoule be kept stable . one line contains a dir or file path , path is relative to the root dest dir path ",required=False , type=argparse.FileType('r'))
    args = argp.parse_args()
    main(args.dependency_file , args.keep_stable_file)

    args.dependency_file.close()
    args.keep_stable_file != None and args.keep_stable_file.close()
