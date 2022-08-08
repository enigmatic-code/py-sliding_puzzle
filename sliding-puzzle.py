#! python
###############################################################################
#
# File:         sliding-puzzle.py
# RCS:          $Header: $
# Description:  Tk Interface to Sliding Puzzle Solver (Enigma 1444)
# Author:       Jim Randell
# Created:      Mon Apr 08 09:37:30 2013
# Modified:     Mon Aug  8 13:11:54 2022 (Jim Randell) jim.randell@gmail.com
# Language:     Python
# Package:      N/A
# Status:       Experimental (Do Not Distribute)
#
# (C) Copyright 2013, Jim Randell, all rights reserved.
#
###############################################################################
# -*- mode: Python; py-indent-offset: 2; -*-

from __future__ import print_function

#
# useful routines from enigma.py <http://www.magwag.plus.com/jim/enigma.html>
#

from itertools import islice

# iterate through iterable <l> in chunks of size <n>
def chunk(s, n):
  i = iter(s)
  while True:
    s = tuple(islice(i, 0, n))
    if not len(s): break
    yield s

# flatten a list of lists
def flatten(l):
  return list(j for i in l for j in i)


#
# the code to solve Enigma 1444 <http://enigmaticcode.wordpress.com/2013/04/06/enigma-1444-backslide/#comment-1957>
# (slightly modified)
#

class Impossible(Exception): pass

class Puzzle(object):

  def __init__(self, m, n, target, initial=None):
    assert m > 1 and n > 1
    if initial is None: initial = list(range(1, m * n)) + [0]
    assert len(initial) == m * n, "invalid initial grid"
    assert len(target) == m * n and target[-1] == 0, "invalid target grid"
    # if m > n flip the puzzle around
    self.flipped = (m > n)
    if self.flipped:
      target = flatten(zip(*chunk(target, m)))
      initial = flatten(zip(*chunk(initial, m)))
      m, n = n, m
    self.m = m
    self.n = n
    self.grid = list(initial)
    self.target = list(target)
    self.b = initial.index(0)
    self.moves = []

  # make a copy of this puzzle
  def copy(self):
    return Puzzle(self.m, self.n, self.target, self.grid)

  # scramble the puzzle
  def scramble(self):
    (g, m) = (self.grid, self.m)
    import random
    random.shuffle(g)
    # count the number of inversions in the grid
    i = sum(1 for i in range(len(g)) if g[i] > 0 for j in range(i + 1, len(g)) if g[j] > 0 and g[i] > g[j])
    b = g.index(0)
    # a puzzle with odd m always has even permutations, for even m it alternates with the row of b
    if (m % 2 == 1 and i % 2 == 1) or (m % 2 == 0 and ((i + b // m) % 2 == 0)):
      # swap two adjacent tiles to correct the parity
      (i, j) = sorted((0, 1, 2), key=lambda x: g[x])[1:3]
      (g[i], g[j]) = (g[j], g[i])
    self.b = b

  # positions adjacent to <p>
  def adjacent(self, p):
    (m, n) = (self.m, self.n)
    (p0, p1) = divmod(p, m)
    if p0 > 0: yield p - m
    if p0 + 1 < n: yield p + m
    if p1 > 0: yield p - 1
    if p1 + 1 < m: yield p + 1

  # move by sliding the tiles at positions <ps>
  def move(self, ps):
    (b, g, ms) = (self.b, self.grid, self.moves)
    for p in ps:
      # check the blank is adjacent to position p
      assert any(b == x for x in self.adjacent(p)), "invalid move"
      # update moves
      ms.append(('M', g[p]))
      # swap the blank and the tile
      g[b], g[p], b = g[p], g[b], p
      # remove any duplicate moves
      for i in range(len(ms) - 2, -1, -1):
        if ms[i][0] == 'M':
          if ms[i] == ms[-1]:
            del ms[-1]
            del ms[i]
          break
    # update blank position
    self.b = b

  # move the blank to one of the positions <ps>
  # without disturbing tiles in positions <fs>
  def blank(self, ps, fs):
    (m, n, g, b) = (self.m, self.n, self.grid, self.b)
    # is the blank already in position?
    if b in ps: return
    # an empty grid to record distances from the blank
    h = [None] * len(g)
    # mark any fixed tiles
    for p in fs: h[p] = m + n
    # and the initial position of the blank
    h[b] = 0
    # and propogate distances from the blank
    d = 0
    while h.count(d) > 0:
      for (p, x) in enumerate(h):
        if x != d: continue
        # mark any adjacent empty squares with d + 1
        for q in self.adjacent(p):
          if h[q] is None: h[q] = d + 1
      d += 1
    # find the position with a minimal distance
    (d, p) = min((h[p], p) for p in ps)
    # now traverse the grid to find the moves needed
    ms = [p]
    while d > 1:
      # find an adjacent square with a distance of d - 1
      d -= 1
      for p in self.adjacent(p):
        if h[p] == d:
          ms.insert(0, p)
          break
    # make the moves
    self.move(ms)

  # place the tile labelled <t> in position <p>
  # without disturbing tiles in positions <fs>
  # (presumed to be in the top row on the left)
  def place(self, t, p, fs):
    self.moves.append(('P', t))
    (g, m) = (self.grid, self.m)
    # find the tile
    s = g.index(t)
    # move the piece to the right (if necessary)
    while s % m < p % m:
      self.blank([s + 1], fs + [s])
      self.move([s])
      s += 1
    # move the piece up (if necessary)
    while s // m > p // m:
      self.blank([s - m], fs + [s])
      self.move([s])
      s -= m
    # move the piece left (if necessary)
    while s % m > p % m:
      self.blank([s - 1], fs + [s])
      self.move([s])
      s -= 1

  # solve a reduced puzzle by removing the top row
  def reduce(self):
    (m, n, g, t) = (self.m, self.n, self.grid, self.target)
    # create a reduced puzzle
    p = Puzzle(m, n - 1, t[m:], initial=g[m:])
    # solve it
    p.solve()
    # and incorporate the results (unflipping as necessary)
    if p.flipped: p.grid = flatten(zip(*chunk(p.grid, p.m)))
    self.grid = self.grid[:m] + p.grid
    self.b = self.grid.index(0)
    self.moves.extend(p.moves)

  # solve a 2x2 grid
  def solve2x2(self):
    # place the right tile in position 0
    self.place(self.target[0], 0, [])
    # and the blank in the bottom right
    self.blank([3], [0])
    # is it solved?
    if self.grid != self.target: raise Impossible

  # solve a 2x3 grid
  def solve2x3(self):
    t = self.target
    # place the right tile in position 0
    self.place(t[0], 0, [])
    # if the next tile is not already in position
    if self.grid.index(t[1]) != 1:
      # get the tile for position 1 in position 3
      self.place(t[1], 3, [0])
      # if the blank is in position 1, just move the piece into place
      if self.b == 1:
        self.move([3])
      else:
        # get the blank into position 2 and then move the piece into position
        self.blank([2], [0, 3])
        self.move([0, 1, 3, 5, 4, 2, 0, 1, 3, 2, 4, 5, 3, 1, 0, 2])
    # and solve the remaining 2x2 grid
    self.reduce()

  # general case solver for larger grids
  def solveit(self):
    (m, n, t) = (self.m, self.n, self.target)
    # get the first m - 1 tiles in the right position
    fs = []
    for i in range(0, m - 1):
      self.place(t[i], i, fs)
      fs.append(i)
    # if the final tile of the row is not in position
    if self.grid.index(t[m - 1]) != m - 1:
      # then get it underneath it's target position
      p = m - 3
      self.place(t[m - 1], p + 2 + m, fs)
      # get the blank in the right position and complete the top row
      if self.b == p + 2:
        self.move([p + 2 + m])
      else:
        self.blank([p + m], fs + [p + 2 + m])
        self.move((p + x for x in (0, 1, 2, 2 + m, 1 + m, 1, 0, m)))
    # and solve the rest of the puzzle
    self.reduce()

  def solve(self):
    (m, n) = (self.m, self.n)
    if (m, n) == (2, 2):
      self.solve2x2()
    elif (m, n) == (2, 3):
      self.solve2x3()
    else:
      self.solveit()
    return self.moves


#
# a Tk UI
#

import sys
import time
import argparse

if sys.version_info[0] == 2:
  from Tkinter import *
else:
  from tkinter import *

DEFAULTS = {
  # colours: background, foreground, highlight
  'bg': 'white', 'fg': 'black', 'hl': 'yellow',
  # fonts
  'font': 'Helvetica',
  # puzzle dimensions
  'm': 10, 'n': 5,
  # size of components
  'padx': 16, 'pady': 16, 'frame': 8, 'border': 4,
  # sliding animation
  'steps': 8, 'delay': 20,
}

class App(Frame):

  def __init__(self):
    self.moving = None
    self.count = 0
    self.moves = []
    self.current_tile = None
    self.placed_tiles = set()
    self.current_position = None
    self.start_time = None
    # arguments
    args = self.args()
    self.m = args.m
    self.n = args.n
    t = args.t
    if len(t) == 0: t = list(range(self.m * self.n - 1, 0, -1))
    if len(t) < self.m * self.n: t += [0]
    self.target_args = (t if len(args.t) > 0 else None)
    self.puzzle = Puzzle(self.m, self.n, t, list(range(1, self.m * self.n)) + [0])
    self.fg = args.fg
    self.bg = args.bg
    self.hl = args.hl
    self.font = args.font
    self.padx = args.padx
    self.pady = args.pady
    self.frame = args.frame
    self.border = args.border
    self.steps = args.steps
    self.delay = args.delay
    self.init()

  def args(self):
    arg = argparse.ArgumentParser(description='Sliding Puzzle.')
    arg.add_argument('-fg', '--foreground', dest='fg', default=DEFAULTS['fg'], help='foreground colour (default: {d})'.format(d=DEFAULTS['fg']))
    arg.add_argument('-bg', '--background', dest='bg', default=DEFAULTS['bg'], help='background colour (default: {d})'.format(d=DEFAULTS['bg']))
    arg.add_argument('-hl', '--highlight', dest='hl', default=DEFAULTS['hl'], help='highlight colour (default: {d})'.format(d=DEFAULTS['hl']))
    arg.add_argument('-fn', '--font', dest='font', default=DEFAULTS['font'], help='font (default: {d})'.format(d=DEFAULTS['font']))
    arg.add_argument('-f', '--frame', dest='frame', type=int, default=DEFAULTS['frame'], help='puzzle frame width (default: {d})'.format(d=DEFAULTS['frame']))
    arg.add_argument('-b', '--border', dest='border', type=int, default=DEFAULTS['border'], help='tile highlight width (default: {d})'.format(d=DEFAULTS['border']))
    arg.add_argument('-px', '--padx', dest='padx', type=int, default=DEFAULTS['padx'], help='puzzle pad x (default: {d})'.format(d=DEFAULTS['padx']))
    arg.add_argument('-py', '--pady', dest='pady', type=int, default=DEFAULTS['pady'], help='puzzle pad y (default: {d})'.format(d=DEFAULTS['pady']))
    arg.add_argument('-s', '--steps', dest='steps', type=int, default=DEFAULTS['steps'], help='number of steps in slide (default: {d})'.format(d=DEFAULTS['steps']))
    arg.add_argument('-d', '--delay', dest='delay', type=int, default=DEFAULTS['delay'], help='ms delay between steps (default: {d})'.format(d=DEFAULTS['delay']))
    arg.add_argument(metavar='M', dest='m', type=int, nargs='?', default=DEFAULTS['m'], help='puzzle width (default: {d})'.format(d=DEFAULTS['m']))
    arg.add_argument(metavar='N', dest='n', type=int, nargs='?', default=DEFAULTS['n'], help='puzzle height (default: {d})'.format(d=DEFAULTS['n']))
    arg.add_argument(metavar='T', dest='t', type=int, nargs='*', help='target configuration')
    return arg.parse_args()


  def init(self, master=None):
    Frame.__init__(self, master)
    # make the application resizable
    top = self.winfo_toplevel()
    top.rowconfigure(0, weight=1)
    top.columnconfigure(0, weight=1)
    self.grid(sticky=N+S+E+W)
    # now create the UI elements
    self.start()


  def start(self):
    self.master.title('Sliding Puzzle')

    # control buttons
    buttons = Frame(self)
    solve_button = Button(buttons, text="Solve", command=self.solve)
    solve_button.pack(side=LEFT, padx=10)
    targets = ['Target: Normal', 'Target: Reversed']
    if self.target_args is not None: targets.append('Target: Command Line')
    self.target = StringVar(self)
    self.target.set(targets[-1])
    target_button = OptionMenu(buttons, self.target, *targets, command=self.set_target)
    target_button.pack(side=LEFT, padx=10)
    scramble_button = Button(buttons, text="Scramble", command=self.scramble)
    scramble_button.pack(side=LEFT, padx=10)
    quit_button = Button(buttons, text="Quit", command=self.quit)
    quit_button.pack(side=RIGHT, padx=10)

    # main display aread
    canvas = Canvas(self, width=640, height=480, background='light grey')

    # message display
    self.message = StringVar(self)
    label = Label(self, textvariable=self.message)

    buttons.grid(column=0, row=0, sticky=N+E+W)
    canvas.grid(column=0, row=1, sticky=N+S+E+W)
    label.grid(column=0, row=2, sticky=S+E+W)
    self.columnconfigure(0, weight=1)
    self.rowconfigure(1, weight=1)

    # interaction, click on the canvas
    canvas.bind('<1>', self.click)
    canvas.bind('<Configure>', self.draw)

    self.canvas = canvas
    self.solve_button = solve_button


  def fill(self, t):
    if t == self.current_tile: return self.hl
    if t in self.placed_tiles: return '#e7e7e7'
    return self.bg

  def flip(self, t):
    return t[::-1] if self.puzzle.flipped else t

  def draw(self, event=None):
    # clear the canvas
    self.canvas.delete(ALL)

    # get the dimensions of the canvas
    cw = self.canvas.winfo_width()
    ch = self.canvas.winfo_height()

    # compute the size of a tile
    (x0, y0, frame, border) = (self.padx, self.pady, self.frame, self.border)
    tile = min((cw - 2 * (x0 + frame) - (self.m + 1) * border) // self.m, (ch - 2 * (y0 + frame) - (self.n + 1) * border) // self.n)
    x0 = (cw - 2 * frame - self.m * (border + tile) - border) // 2
    y0 = (ch - 2 * frame - self.n * (border + tile) - border) // 2
    font = [self.font, tile // 2, 'bold']

    # draw the frame
    (fw, fh, fb) = (self.m * (tile + border) + border, self.n * (tile + border) + border, frame // 2)
    self.canvas.create_rectangle(x0 + fb, y0 + fb, x0 + fw + 3 * fb, y0 + fh + 3 * fb, outline=self.fg, width=frame)

    # draw any current position
    (x0, y0) = (x0 + frame, y0 + frame)
    if self.current_position is not None:
      (i, j) = self.flip(divmod(self.current_position, self.puzzle.m))
      (x, y, b) = (x0 + j * (tile + border), y0 + i * (tile + border), border // 2)
      self.canvas.create_rectangle(x + b, y + b, x + tile + 3 * b, y + tile + 3 * b, outline=self.hl, width=border)

    # draw the tiles
    for i in range(self.n):
      for j in range(self.m):
        (x, y) = (x0 + j * (tile + border) + border, y0 + i * (tile + border) + border)
        p = (j * self.puzzle.m + i if self.puzzle.flipped else i * self.puzzle.m + j)
        t = self.puzzle.grid[p]
        if t == 0 or p == self.moving: continue
        tag = 'pos=' + str(p)
        self.canvas.create_rectangle(x + 1, y + 1, x + tile - 1, y + tile - 1, outline=self.fg, fill=self.fill(t), width=2, tags=tag)
        self.canvas.create_text(x + tile // 2, y + tile // 2, text=t, font=font, tags=tag)

    # draw any moving tile
    if self.moving is not None:
      t = self.puzzle.grid[self.moving]
      (i, j) = self.flip(divmod(self.moving, self.puzzle.m))
      (x, y) = (x0 + j * (tile + border) + border, y0 + i * (tile + border) + border)
      (xo, yo) = (tile * self.offset[0] * self.offset[2] // self.steps, tile * self.offset[1] * self.offset[2] // self.steps)
      self.canvas.create_rectangle(x + xo + 1, y + yo + 1, x + tile + xo - 1, y + tile + yo - 1, outline=self.fg, fill=self.fill(t), width=2)
      self.canvas.create_text(x + tile // 2 + xo, y + tile // 2 + yo, text=t, font=font)

  # move the tile at position p
  def move(self, p):
    if self.puzzle.b not in self.puzzle.adjacent(p): return
    self.moving = p
    if self.puzzle.b == p + self.puzzle.m: (x, y) = (0, 1)
    if self.puzzle.b == p - self.puzzle.m: (x, y) = (0, -1)
    if self.puzzle.b == p + 1: (x, y) = (1, 0)
    if self.puzzle.b == p - 1: (x, y) = (-1, 0)
    self.offset = list(self.flip((x, y))) + [0]
    # set a timer to update the offset
    self.after(self.delay, self.slide)

  def automate(self, moves):
    while len(moves) > 0:
      m = moves.pop(0)
      if m[0] == 'M':
        self.move(self.puzzle.grid.index(m[1]))
        break
      elif m[0] == 'P':
        if self.current_tile is not None:
          self.placed_tiles.add(self.current_tile)
        self.current_tile = m[1]
        self.current_position = self.puzzle.target.index(self.current_tile)
    if len(moves) == 0:
      self.current_tile = self.current_position = None
      self.placed_tiles = set()
      self.set_message()
      self.stop()
    self.moves = moves

  def set_message(self):
    elapsed = (0 if self.start_time is None else int(time.time() - self.start_time))
    (m, s) = divmod(elapsed, 60)
    state = ('[SOLVED] ' if self.puzzle.grid == self.puzzle.target else '')
    self.message.set("{state}Moves: {n}, Elapsed Time: {m:1d}m{s:02d}s".format(state=state, n=self.count, m=m, s=s))

  def slide(self):
    if self.offset[2] < self.steps:
      self.offset[2] += 1
      self.after(self.delay, self.slide)
    else:
      self.puzzle.move([self.moving])
      self.moving = None
      self.automate(self.moves)
      self.count += 1
      self.set_message()
    self.draw()

  def click(self, event):
    w = event.widget.find_withtag(CURRENT)
    if not w: return
    for tag in event.widget.gettags(w):
      if tag.startswith('pos='):
        p = int(tag[4:])
        if self.start_time is None: self.start_time = time.time()
        self.move(p)
    self.draw()

  def scramble(self):
    self.puzzle.scramble()
    self.count = 0
    self.start_time = None
    self.set_message()
    self.draw()

  def set_target(self, value):
    if value == 'Target: Normal':
      target = list(range(1, self.m * self.n)) + [0]
    if value == 'Target: Reversed':
      target = list(range(self.m * self.n - 1, 0, -1)) + [0]
    if value == 'Target: Command Line':
      target = self.target_args
    self.puzzle.target = (flatten(zip(*chunk(target, self.m))) if self.puzzle.flipped else target)
    self.set_message()
    self.draw()

  def solve(self):
    # make a copy of the puzzle to determine the moves
    p = self.puzzle.copy()
    try:
      self.count = 0
      self.start_time = time.time()
      self.solve_button.configure(text='Stop', command=self.stop)
      self.automate(p.solve())
    except Impossible:
      self.message.set("Impossible Target")
      self.stop()
      self.bell()

  def stop(self):
    self.moves = []
    self.solve_button.configure(text='Solve', command=self.solve)


def main():
  # create the UI
  app = App()
  app.draw()
  app.mainloop()

if __name__ == '__main__':
  main()
