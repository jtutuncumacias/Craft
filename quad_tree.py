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

def build_pool(data):
  return build(data[0], data[1], data[2], data[3], data[4])

def build(chunks, minp, minq, maxp, maxq):
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

    p_pivot = int((minp + maxp) * 0.5)
    q_pivot = int((minq + maxq) * 0.5)

    for chunk in chunks:
      if chunk.p < p_pivot:
        if chunk.q < q_pivot:
          c0.append(chunk)
        else:
          c2.append(chunk)
      else:
        if chunk.q < q_pivot:
          c1.append(chunk)
        else:
          c3.append(chunk)

    data = [(c0, minp, minq, p_pivot, q_pivot), (c1, p_pivot, minq, maxp, q_pivot), (c2, minp, q_pivot, p_pivot, maxq), (c3, p_pivot, q_pivot, maxp, maxq)]

    pool = multiprocessing.Pool(4)
    node.children = list(pool.map(build_pool,data))
    pool.close()
    pool.join()

  return node


CHUNK_SIZE = 32

def chunked(x):
    return int(floor(round(x) / CHUNK_SIZE))

def box_point_distance(minp, minq, maxp, maxq, p, q):
    dp = max(max(minp - p, p - maxp), 0)
    dq = max(max(minq - q, q - maxq), 0)
    return dp**2 + dq**2

class Chunk():
  def __init__(self, p, q):  
    self.p = p
    self.q = q
    self.clients = []
  def output(self):
    return "p: {}, q: {}, clients: {}".format(self.p, self.q, ', '.join(str(id) for id in self.clients))
  def __repr__(self):
    return self.output()
  def __str__(self):
    return self.output()

class Node():
  def __init__(self):
    self.isLeaf = False
    self.chunks = []
    self.children = []

class QuadTree():
  def __init__(self, chunks):
    chunks = list(chunks.values())

    minint = -sys.maxint - 1
    self.minp = sys.maxint
    self.minq = sys.maxint
    self.maxp = minint
    self.maxq = minint

    for chunk in chunks:
      self.minp = min(self.minp, chunk.p)
      self.minq = min(self.minq, chunk.q)
      self.maxp = max(self.maxp, chunk.p)
      self.maxq = max(self.maxq, chunk.q)

    self.root = build(chunks, self.minp, self.minq, self.maxp, self.maxq)

  def getClients(self, clients_dict, p, q, radius):
    return self.getClientsImpl(clients_dict, self.root, self.minp, self.minq, self.maxp, self.maxq, p, q, radius)

  def getClientsImpl(self, clients_dict, node, minp, minq, maxp, maxq, p, q, radius):
    clients = []
    if node.isLeaf:
      for chunk in node.chunks:
        for client in chunk.clients:
          if (chunked(clients_dict[client].position[0]) - p)**2 + (chunked(clients_dict[client].position[2]) - q)**2 <= radius**2:
            clients.append(clients_dict[client])
    else:
      p_pivot = int((minp + maxp) * 0.5)
      q_pivot = int((minq + maxq) * 0.5)
      p_size = int((maxp - minp) * 0.5)
      q_size = int((maxq - minq) * 0.5)

      for i in range(4):
        childminp = 0
        childminq = 0
        if i == 1 or i == 3:
            childminp = p_pivot
        else:
            childminp = minp
        if i > 1:
            childminq = q_pivot
        else:
            childminq = minq

        if box_point_distance(childminp, childminq, childminp + p_size, childminq + q_size, p, q) <= radius**2:
          clients.extend(self.getClientsImpl(clients_dict, node.children[i], childminp, childminq, childminp + p_size, childminq + q_size, p, q, radius))

    return clients