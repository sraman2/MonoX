#!/usr/bin/env python

import sys

from argparse import ArgumentParser

argParser = ArgumentParser(description = 'Spit out plots showing shape variations.')
# argParser.add_argument('model', metavar = 'MODEL', help = 'Signal model name. Use "nomodel" for model-independent limits.')
argParser.add_argument('input', metavar = 'PATH', help = 'Histogram ROOT file.')
argParser.add_argument('--variable', '-v', action = 'store', metavar = 'VARIABLE', dest = 'variable', default = 'phoPtHighMet', help = 'Discriminating variable.')

args = argParser.parse_args()
sys.argv = []

import os
import array
import math
import re
import ROOT as r 
from pprint import pprint

r.gROOT.SetBatch(True)

thisdir = os.path.dirname(os.path.realpath(__file__))
basedir = os.path.dirname(thisdir)
sys.path.append(basedir)
from plotstyle import *
from datasets import allsamples
import config
from main.plotconfig import getConfig

monophConfig = getConfig(args.input)
source = r.TFile.Open(config.histDir + '/plots/' + args.input + '.root')

variable = args.variable
xtitle = monophConfig.getPlot(variable).title

lumi = 0.
for sName in monophConfig.obs.samples:
    lumi += allsamples[sName.name].lumi

def getHist(name, syst = ''):
    if syst:
        return source.Get(variable + '/' + name + '_' + syst)
    else:
        return source.Get(variable + '/' + name)

# gather process names
processes = [g.name for g in monophConfig.bkgGroups] # [args.model] +

# get nuisances
nuisances = {}
for key in source.Get(variable).GetListOfKeys():
    matches = re.match('([0-9a-zA-Z-]+)_([0-9a-zA-Z]+)(Up|Var)', key.GetName())
    if not matches:
        continue

    proc = matches.group(1)
    syst = matches.group(2)
    vartype = matches.group(3)

    if proc not in processes:
        continue

    if vartype == 'Up' and not getHist(proc, syst + 'Down'):
        continue

    if syst not in nuisances:
        nuisances[syst] = [proc]
    else:
        nuisances[syst].append(proc)

pprint(nuisances)


rcanvas = RatioCanvas(lumi = lumi)

for syst, procs in nuisances.items():
    plotDir = 'monophoton/shapeSysts/' + '/' + args.input
    for proc in processes:
        if proc in procs:
            rcanvas.Clear()
            rcanvas.legend.Clear()
            rcanvas.legend.setPosition(0.6, 0.7, 0.9, 0.9)
            rcanvas.xtitle = xtitle

            nominal = getHist(proc)
            up = getHist(proc, syst + 'Up')
            down = getHist(proc, syst + 'Down')
            var = getHist(proc, syst + 'Var')

            nominal.GetXaxis().SetTitle('E_{T}^{#gamma} (GeV)')
            rcanvas.legend.add('nominal', title = 'Nominal', lcolor = r.kBlack, lwidth = 2)
            rcanvas.legend.apply('nominal', nominal)
            nomId = rcanvas.addHistogram(nominal, drawOpt = 'L')

            if not var:
                rcanvas.rlimits = (0.95, 1.05)
                for iB in range(1, up.GetNbinsX()+1):
                    if nominal.GetBinContent(iB):
                        binRatioUp = up.GetBinContent(iB) / nominal.GetBinContent(iB)
                        binRatioDown = down.GetBinContent(iB) / nominal.GetBinContent(iB)
                    else:
                        binRatioUp = 0.
                        binRatioDown = 1.
                    
                    if binRatioUp > 1.55 or binRatioDown < 0.45:
                        rcanvas.rlimits = (0.0, 2.0)
                        break

                    elif binRatioUp > 1.2 or binRatioDown < 0.8:
                        rcanvas.rlimits = (0.45, 1.55)

                    elif binRatioUp > 1.05 or binRatioDown < 0.95:
                        rcanvas.rlimits = (0.8, 1.2)
                    

                up.GetXaxis().SetTitle('E_{T}^{#gamma} (GeV)')
                rcanvas.legend.add('up', title = 'Up', lcolor = r.kRed, lwidth = 2)
                rcanvas.legend.apply('up', up)
                upId = rcanvas.addHistogram(up, drawOpt = 'L')

                down.GetXaxis().SetTitle('E_{T}^{#gamma} (GeV)')
                rcanvas.legend.add('down', title = 'Down', lcolor = r.kBlue, lwidth = 2)
                rcanvas.legend.apply('down', down)
                downId = rcanvas.addHistogram(down, drawOpt = 'L')

                rcanvas.printWeb(plotDir + '/' + proc, syst, hList = [upId, downId, nomId], rList = [nomId, upId, downId])

            else:
                var.GetXaxis().SetTitle('E_{T}^{#gamma} (GeV)')
                rcanvas.legend.add('var', title = 'Var', lcolor = r.kRed, lwidth = 2)
                rcanvas.legend.apply('var', var)
                varId = rcanvas.addHistogram(var, drawOpt = 'L')

                rcanvas.printWeb(plotDir + '/' + proc, syst, hList = [varId, nomId], rList = [nomId, varId])
