from math import floor
from world import World
import Queue
import SocketServer
import datetime
import random
import re
import requests
import sqlite3
import sys
import multiprocessing
import time
import traceback
import matplotlib.pyplot as plt
import matplotlib.patches as patches

class Node():
  def __init__(self):
    self.isLeaf = False
    self.chunks = []
    self.children = []

class QuadTree():
  def __init__(self, chunks):
    minint = -sys.maxint - 1

    bminx = minint
    bminy = minint
    bmaxx = sys.maxint
    bmaxy = sys.maxint

    for chunk in chunks:
      bminx = min(bminx, chunk[0])
      bminy = min(bminy, chunk[1])
      bmaxx = max(bminx, chunk[0])
      bmaxy = max(bmaxy, chunk[1])

    self.root = self.build(chunks, bminx, bminy, bmaxx, bmaxy)


  def build_pool(self, data):
    return self.build(data[0], data[1], data[2], data[3], data[4])

  def build(self, chunks, bminx, bminy, bmaxx, bmaxy):
    node = Node()

    if len(chunks) < 2:
      node.isLeaf = True
      node.chunks = chunks
    else:
      node.isLeaf = False

      c0 = []
      c1 = []
      c2 = []
      c3 = []

      x_pivot = int((bminx + bmaxx) * 0.5)
      y_pivot = int((bminy + bmaxy) * 0.5)

      for chunk in chunks:
        if chunk[0] < x_pivot:
          if chunk[1] < y_pivot:
            c0.append(chunk)
          else:
            c2.append(chunk)
        else:
          if chunk[1] < y_pivot:
            c1.append(chunk)
          else:
            c3.append(chunk)

      data = [(c0, bminx, bminy, x_pivot, y_pivot), (c1, x_pivot, bminy, bmaxx, y_pivot), (c2, bminx, y_pivot, x_pivot, bmaxy), (c3, x_pivot, y_pivot, bmaxx, bmaxy)]

      pool = multiprocessing.Pool(4)
      node.children = list(pool.map(build_pool, data))

    return node
    