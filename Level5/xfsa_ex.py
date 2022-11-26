﻿# -*- coding: utf-8 -*-

################################################################################
# Copyright © 2017 BlackDragonHunt
# This work is free. You can redistribute it and/or modify it under the
# terms of the Do What The Fuck You Want To But It's Not My Fault Public
# License, Version 1, as published by Ben McGinnes. See the COPYING file
# for more details.
################################################################################

import os

from util import *
from level5_dec import *

XFSA_MAGIC = "XFSA"

def xfsa_ex(filename, out_dir = None):
  out_dir = out_dir or os.path.splitext(filename)[0]
  
  f = BinaryFile(filename, "rb")
  
  if not f.read(4) == XFSA_MAGIC:
    print("Invalid XFSA file.")
    f.close()
    return
  
  dir_tbl_off  = f.get_u32()
  unk_tbl_off  = f.get_u32()
  file_tbl_off = f.get_u32()
  fn_table_off = f.get_u32()
  data_off     = f.get_u32()
  
  # Read our tables...
  f.seek(dir_tbl_off)
  dir_tbl = f.read(unk_tbl_off - dir_tbl_off)
  dir_tbl = level5_dec(dir_tbl)
  dir_tbl_size = len(dir_tbl)
  dir_tbl = BinaryString(dir_tbl)
  
  f.seek(unk_tbl_off)
  unk_tbl = f.read(file_tbl_off - unk_tbl_off)
  unk_tbl = level5_dec(unk_tbl)
  unk_tbl_size = len(unk_tbl)
  unk_tbl = BinaryString(unk_tbl)
  
  f.seek(file_tbl_off)
  file_tbl = f.read(fn_table_off - file_tbl_off)
  file_tbl = level5_dec(file_tbl)
  file_tbl_size = len(file_tbl)
  file_tbl = BinaryString(file_tbl)
  
  f.seek(fn_table_off)
  fn_table = f.read(data_off - fn_table_off)
  fn_table = level5_dec(fn_table)
  fn_table_size = len(fn_table)
  fn_table = BinaryString(fn_table)
  
  # Parse through the directory table, which leads us to our other tables.
  for i in range(dir_tbl_size / 0x10):
    dir_crc = dir_tbl.get_u32()
    
    val          = dir_tbl.get_u32()
    fn_off_base  = val >> 14
    file_count   = val & 0x3FFF
    
    file_id      = dir_tbl.get_u16()
    subdir_id    = dir_tbl.get_u16()
    
    val          = dir_tbl.get_u32()
    dir_off      = val >> 14
    subdir_count = val & 0x3FFF
    
    fn_table.seek(dir_off)
    dirname = fn_table.get_str()
    
    # print "{:<40}".format(dirname),
    # # print "{:<40}".format(item),
    # print "0x%04X  " % subdir_id,
    # print "0x%04X  " % subdir_count,
    # print "0x%04X  " % file_id,
    # print "0x%04X  " % file_count,
    # print "0x%08X  " % fn_off_base,
    # print "0x%08X" % dir_off
    
    dirname = os.path.join(out_dir, dirname)
    try:
      os.makedirs(dirname)
    except:
      pass
    
    # Okay, so, uh. The dir table is sorted by CRC, for whatever reason. But it
    # also stores the index into the file table where this dir's data begins.
    # Then the file table stores offsets to filenames relative to fn_off_base
    # given in this directory entry--only they're not in order, so we can't
    # split these steps into more manageable chunks.
    file_tbl.seek(file_id * 0x0C)
    for j in range(file_count):
      fn_crc = file_tbl.get_u32()
      val1 = file_tbl.get_u32()
      val2 = file_tbl.get_u32()
      
      # Our values here are packed sort of weirdly.
      # xxxxxxyy yyyyyyyy yyyyyyyy yyyyyyyy xxxxxxxx xzzzzzzz zzzzzzzz zzzzzzzz
      # x -> filename offset, relative to dirname entry
      # y -> file offset
      # z -> file size
      file_data_off = (val1 & 0x3FFFFFF) << 4
      file_size     = val2 & 0x7FFFFF
      fn_off        = ((val1 >> 26) << 9) | (val2 >> 23)
      
      fn_table.seek(fn_off + fn_off_base)
      fn = fn_table.get_str()
      fn = os.path.join(dirname, fn)
      
      f.seek(file_data_off + data_off)
      data = f.read(file_size)
      
      print(" ->", fn)
      # print "{:<60}".format(fn),
      # print "0x%08X  " % fn_off,
      # print "0x%08X  " % file_data_off,
      # print "0x%08X  " % file_size
      
      with open(fn, "wb") as f2:
        f2.write(data)
  
  f.close()

if __name__ == "__main__":
  # xfsa_ex("fa/vs1.fa")
  for fn in list_all_files("fa"):
    ext = os.path.splitext(fn)[1].lower()
    
    if not ext == ".fa":
      continue
    
    print(fn)
    xfsa_ex(fn)
    print()

### EOF ###