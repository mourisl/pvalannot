import seaborn as sns
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import scipy as sp
import math

def DrawPvalueBracket(x0, x1, y, h, p, font_scale, ax, renderer, textKwargs):
    ax.plot([x0, x0, x1, x1], [y, y+h, y+h, y], lw=1, color="black", scalex=False, clip_on=False)
    t = ax.text((x0+x1)/2, y+h + h/2, p, ha='center', va='baseline', color="black", **textKwargs) 
    #t = ax.annotate(text = p, xy=((x0+x1)/2, y+h))
    # return two boexes, one for brackett, one for text, and the text object itself
    if (font_scale != 1):
        fontSize = t.get_fontsize()
        t.set_fontsize(font_scale * fontSize)
    
    tbox = t.get_window_extent(renderer).transformed(ax.transData.inverted())
    left, right = ax.get_xlim()
    hmargin = (right - left) / 60
    if (tbox.x0 < left + hmargin):
        t.remove()
        t = ax.text(left+hmargin, y+h + h/2, p, ha='left', va='baseline', color="black", **textKwargs) 
        tbox = t.get_window_extent(renderer).transformed(ax.transData.inverted())
    elif (tbox.x1 + hmargin > right):
        t.remove()
        t = ax.text(right - hmargin, y+h + h/2, p, ha='right', va='baseline', color="black", **textKwargs) 
        tbox = t.get_window_extent(renderer).transformed(ax.transData.inverted())
        
    return (x0, y, x1, y + h), \
            (tbox.x0, tbox.y0, tbox.x1, tbox.y1), t
    
def FormatPString(fmt, stats, pval, non_sig_fmt, significant_p, styles = None):
    if (pval < significant_p):
        if ("trend_arrow" in styles):
            if (stats < 0):
                fmt += r" $\searrow$"
            else:
                fmt += r" $\nearrow$"
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
    if (xOrder is None):
        xOrder = data[x].unique()
    if (hue != None and hueOrder is None):
        hueOrder = data[hue].unique()
    if (hue is None):
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

def AddPvalAnnot(x, y, data, pairs = None, ax = None, hue = None, func = None, order = None, 
                 hue_order = None, font_scale = 1, fmt = None, fig = None, padjust_func = None, 
                 pair_test_key = None, significant_p = 0.05, margin=None, styles = None, change_ylim=True,
                 func_args = None):
    # Get the canvas attributes.
    ax = ax or plt.gca()
    fig = fig or ax.get_figure()
    renderer = fig.canvas.get_renderer()
    
    # obtain the x coordinate for each x.
    xCoord, xCoordRank, xCoordRankHeight = BuildXCoord(x, y, hue, order, hue_order, data)
    
    # Get some drawing parameter based on the axis and data size
    bot, top = ax.get_ylim()
    h = (top - bot) / 30
    margin = margin or h / 2
    
    # These parameters will be determined after drawing the first bracket
    fontWidth = 0
    fontHeight = 0
    
    if (func is None):
        func = sp.stats.mannwhitneyu
    if (func_args is None):
        func_args = {}
    if (fmt is None):
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
    
    # Infer our own pairss
    if (pairs == None):
        pairs = []
        vx = order or data[x].unique()
        if (hue is None):
            for i in range(len(vx)):
                for j in range(i + 1, len(vx)):
                    pairs.append([vx[i], vx[j]])
        else:
            vhue = hue_order or data[hue].unique()
            for xitem in vx:
                for i in range(len(vhue)):
                    for j in range(i + 1, len(vhue)):
                        pairs.append([(xitem, vhue[i]), (xitem, vhue[j])])                
    
    boxes = []
    drawed = False
    statsList = []
    pvalList = []
    textList = []
    for i, p in enumerate(sorted(pairs, key=lambda p: (min(xCoord[p[0]], xCoord[p[1]]), 
                                                      max(xCoord[p[0]], xCoord[p[1]])))):
        # Here x, y stands for the cateogry of pair[0] and pair[1]
        xSubDf = []
        ySubDf = []
        if (hue is None):
            xSubDf = data.loc[data[x] == p[0]]
            ySubDf = data.loc[data[x] == p[1]]
        else:
            xSubDf = data.loc[(data[x] == p[0][0]) & (data[hue] == p[0][1])]
            ySubDf = data.loc[(data[x] == p[1][0]) & (data[hue] == p[1][1])]
            
        xv = []
        yv = []
        if (pair_test_key is None):
            xv = xSubDf[y].dropna()
            yv = ySubDf[y].dropna()
        else: # paired test
            joinedDf = xSubDf.set_index(pair_test_key).join(ySubDf.set_index(pair_test_key), 
                lsuffix = "_0", rsuffix = "_1").dropna(subset = [str(y) + "_0", str(y) + "_1"])
            xv = joinedDf[str(y) + "_0"]
            yv = joinedDf[str(y) + "_1"]
           
        if (len(xv) == 0 or len(yv) == 0):
            pvalList.append(-1)
            statsList.append(-1)
            continue
        
        if (xCoord[p[0]] < xCoord[p[1]]):
            stats, pval = func(xv, yv, **func_args)
        else:
            stats, pval = func(yv, xv, **func_args)
        pvalList.append(pval)
        statsList.append(stats)
    
    if (padjust_func is not None):
        tmpList = []
        for p in pvalList:
            if (p != -1):
                tmpList.append(p)
        tmpList = padjust_func(tmpList)
        k = 0
        for i, p in enumerate(pvalList):
            if (p != -1):
                pvalList[i] = tmpList[k] 
                k += 1
                
    ret = {}
    for i, p in enumerate(sorted(pairs, key=lambda p: (min(xCoord[p[0]], xCoord[p[1]]), 
                                                      max(xCoord[p[0]], xCoord[p[1]])))):
        if (pvalList[i] == -1):
            continue
        stats = statsList[i]
        pval = pvalList[i]
        coord0 = min(xCoord[p[0]], xCoord[p[1]])
        coord1 = max(xCoord[p[0]], xCoord[p[1]])
        rank0 = xCoordRank[coord0]
        rank1 = xCoordRank[coord1]
        base = max(xCoordRankHeight[rank0:(rank1+1)]) + margin
        ret[(p[0], p[1])] = (stats, pval)
        if (pval < significant_p or not hide_nonsig):
            finalBox = [0, 0, 0, 0]
            if (len(drawnBrackets) > 0):
                # Check whether it overlaps with previous drawn rectangles
                textSize = fontWidth * (len(FormatPString(fmt, stats, pval, non_sig_fmt, significant_p, styles))+0.5)
                start = min(coord0, (coord0 + coord1) / 2 - textSize / 2)
                end = max(coord1, (coord0 + coord1) / 2 + textSize / 2)
                while (True):
                    box = [start, base, end, base + h + fontHeight + h/2]
                    newBase = base
                    overlapCount = 0
                    for prevBox in drawnBrackets:
                        if (BoxIntersect(box, prevBox, margin)):
                            if (prevBox[3] + margin > newBase):
                                newBase = prevBox[3] + margin
                            overlapCount += 1
                    if (overlapCount > 0):
                        base = newBase
                    else:
                        break
                finalBox = [start, base, end, base + h + fontHeight]

            textKwargs = {}
            if ("bold_significant" in styles and pval < significant_p):
                textKwargs["fontweight"] = "bold"
            bracketRect, textRect, t = DrawPvalueBracket(coord0, coord1, base, h, 
                              FormatPString(fmt, stats, pval, non_sig_fmt, significant_p, styles), font_scale, 
                              ax, renderer, textKwargs)
            textList.append(t)
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
    if (change_ylim):
        if (maxY > top):
            fontSize = textList[0].get_fontsize()
            origTextBox = textList[0].get_window_extent(renderer).transformed(ax.transData.inverted())
            ax.set(ylim=(bot, maxY))
            newTextBox = textList[0].get_window_extent(renderer).transformed(ax.transData.inverted())
            changeLimRescale = math.pow((origTextBox.y1 - origTextBox.y0)/(newTextBox.y1 - newTextBox.y0), 0.75)
            [textList[i].set_fontsize(fontSize * changeLimRescale) for i in range(len(textList))]
            #updatedTextBox = textList[0].get_window_extent(renderer).transformed(ax.transData.inverted())
            #print(origTextBox, newTextBox, updatedTextBox, changeLimRescale)
    else:
        ax.set(ylim=(bot, top))
    return ret