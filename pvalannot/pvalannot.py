import seaborn as sns
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import scipy as sp

def DrawPvalueBracket(x0, x1, y, h, p, ax, renderer):
    ax.plot([x0, x0, x1, x1], [y, y+h, y+h, y], lw=1, color="black")
    t = ax.text((x0+x1)/2, y+h, p, ha='center', va='bottom', color="black") 
    #t = ax.annotate(text = p, xy=((x0+x1)/2, y+h))
    # return two boexes, one for brackett, one for text
    tbox = t.get_window_extent(renderer).transformed(ax.transData.inverted())
    #print(tbox)
    return (x0, y, x1, y + h), \
            (tbox.x0, tbox.y0, tbox.x1, tbox.y1)
    #print("hi", t.get_window_extent(renderer).transformed(ax.transData.inverted()))
    
def FormatPString(fmt, stats, pval, non_sig_fmt, significant_p, styles = None):
    if (pval < significant_p):
        if ("trend_arrow" in styles):
            if (stats < 0):
                fmt += r" $\nearrow$"
            else:
                fmt += r" $\searrow$"
        return fmt%pval
    else:
        return non_sig_fmt%pval
    
# Test whether two boxes overlaps
# where we also allow margin distance between two boxes
def BoxIntersect(b0, b1, margin):
    if (b0[2] <= b1[0] - margin or b0[0] >= b1[2] + margin):
        return False
    if (b0[3] <= b1[1] - margin or b0[1] >= b1[3] + margin):
        return False
    return True

# @return: the x coordinate for each combination,
#          the coordinate map back to the rank,
#          the list of height for each x coordinate 
def BuildXCoord(x, y, hue, xOrder, hueOrder, data):
    xCoord = {}
    xCoordRank = {}
    xCoordRankHeight = []
    if (xOrder == None):
        xOrder = data[x].unique()
    if (hue != None and hueOrder == None):
        hueOrder = data[hue].unique()
    if (hue == None):
        for i, vx in enumerate(xOrder):
            xCoord[vx] = i
            xCoordRank[i] = i
            xCoordRankHeight.append(data.loc[data[x]==vx, y].max())
    else:    
        block = 0.8 / len(hueOrder)
        k = 0
        for i, vx in enumerate(xOrder):
            for j, vhue in enumerate(hueOrder):
                coord = i - 0.4 + (j + 0.5) * block 
                xCoord[(vx, vhue)] = coord
                xCoordRank[coord] = k
                xCoordRankHeight.append(data.loc[(data[x]==vx) & (data[hue]==vhue), y].max())
                k += 1
    return xCoord, xCoordRank, xCoordRankHeight

def AddPvalAnnot(x, y, data, pairs, ax, hue = None, func = None, order = None, 
                 hue_order = None, fmt = None, fig = None, adjust_func = None, 
                 significant_p = 0.05, styles = None):
    # obtain the x coordinate for each x.
    xCoord, xCoordRank, xCoordRankHeight = BuildXCoord(x, y, hue, order, hue_order, data)
    
    # Get some drawing parameter based on the axis and data size
    bot, top = ax.get_ylim()
    h = (top - bot) / 30
    margin = h / 2
    
    # These parameters will be determined after drawing the first bracket
    fontWidth = 0
    fontHeight = 0
    
    if (func == None):
        func = sp.stats.ranksums
    if (fmt == None):
        fmt = "%.2e"
        
    fmt_no_value = False    
    if ("%" not in fmt):
        fmt_no_value = True
        
    non_sig_fmt = fmt
    if (fmt_no_value):
        non_sig_fmt = "ns"
    
    show_trend_arrow = False
    hide_nonsig = False
    
    if (styles is None):
        styles = []
    for style in styles:
        if (style == "trend_arrow"):
            show_trend_arrow = True
        elif (style == "hide_nonsig"):
            hide_nonsig = True
    drawnBrackets = [] # Store a quadruple for each drawn pvalue bracket,
                      # (x0, y0, x1, y1): 0 lower left corner, 1 upper right corner

    renderer = fig.canvas.get_renderer()
    boxes = []
    drawed = False
    for i, p in enumerate(sorted(pairs, key=lambda p: (min(xCoord[p[0]], xCoord[p[1]]), 
                                                      max(xCoord[p[0]], xCoord[p[1]])))):
        if (hue == None):
            xv = data.loc[data[x] == p[0], y]
            yv = data.loc[data[x] == p[1], y]
        else:
            xv = data.loc[(data[x] == p[0][0]) & (data[hue] == p[0][1]), y]
            yv = data.loc[(data[x] == p[1][0]) & (data[hue] == p[1][1]), y]
        if (len(xv) == 0 or len(yv) == 0):
            continue
            
        coord0 = min(xCoord[p[0]], xCoord[p[1]])
        coord1 = max(xCoord[p[0]], xCoord[p[1]])
        rank0 = xCoordRank[coord0]
        rank1 = xCoordRank[coord1]
        base = max(xCoordRankHeight[rank0:(rank1+1)]) + margin
        
        if (xCoord[p[0]] < xCoord[p[1]]):
            stats, pval = func(xv, yv)
        else:
            stats, pval = func(yv, xv)
            
        if (len(drawnBrackets) > 0):
            # Check whether it overlaps with previous drawn rectangles
            textSize = fontWidth * len(FormatPString(fmt, stats, pval, non_sig_fmt, significant_p, styles))
            start = min(coord0, (coord0 + coord1) / 2 - textSize / 2)
            end = max(coord1, (coord0 + coord1) / 2 + textSize / 2)
            while (True):
                box = [start, base, end, base + h]
                newBase = 0
                overlapCount = 0
                for prevBox in drawnBrackets:
                    if (BoxIntersect(box, prevBox, margin)):
                        if (overlapCount == 0):
                            newBase = prevBox[3] + margin
                        overlapCount += 1
                if (overlapCount > 0):
                    base = newBase
                else:
                    break
        #if (p[0][0] == 1):
        #print(i, p, base, coord0, coord1)
        if (pval < significant_p or not hide_nonsig):
            bracketRect, textRect = DrawPvalueBracket(coord0, coord1, base, h, 
                              FormatPString(fmt, stats, pval, non_sig_fmt, significant_p, styles), 
                              ax, renderer)
            # Use the first drawing to get some statistics about sizes
            if (len(drawnBrackets) == 0):
                fontHeight = textRect[3] - textRect[1]
                fontWidth = (textRect[2] - textRect[0]) / \
                        len(FormatPString(fmt, stats, pval, non_sig_fmt, significant_p, styles))
            drawnBrackets.append(bracketRect)
            drawnBrackets.append(textRect)
        
    # We may need to adjust the axis boundary
    maxY = top
    for box in drawnBrackets:
        if (box[3] + h > maxY):
            maxY = box[3] + h
    if (maxY > top):
        ax.set_ylim((bot, maxY))