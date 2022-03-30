import seaborn as sns
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import scipy as sp

def DrawPvalueBracket(x0, x1, y, h, p, ax):
    ax.plot([x0, x0, x1, x1], [y, y+h, y+h, y], lw=1, color="black")
    ax.text((x0+x1)/2, y+h, p, ha='center', va='bottom', color="black") 


def AddPvalAnnot(x, y, data, pairs, ax, hue = None, func = None, order = None, fmt=None):
    # obtain the x coordinate for each x.
    xCoord = {}
    if (order == None):
        for i, vx in enumerate(data[x].unique()): 
            xCoord[vx] = i
    else:
        for i, vx in enumerate(order):
            xCoord[vx] = i
            
    # Get some drawing parameter based on the axis and data size
    bot, top = ax.get_ylim()
    base = df[y].max()
    h = (top - bot) / 30
    
    if (func == None):
        func = sp.stats.ranksums
    if (fmt == None):
        fmt = "%.2e"
    
    drawnBracket = [] # Store a quadruple for each drawn pvalue bracket,
                      # (x0, y0, x1, y1): 0 lower left corner, 1 upper right corner
    for i, p in enumerate(pairs):
        xv = df.loc[df[x] == p[0], y]
        yv = df.loc[df[x] == p[1], y]
        if (len(xv) == 0 or len(yv) == 0):
            continue
        pval = func(xv, yv)[1]
        AddPvalue(xCoord[p[0]], xCoord[p[1]], base + i * 1.2 * h, h, fmt%pval, ax)
    return
	
