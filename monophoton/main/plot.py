#!/usr/bin/env python

import sys
import os
import collections
import array
import math
import ROOT

basedir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.append(basedir)
from plotstyle import *
from datasets import allsamples

ROOT.gROOT.SetBatch(True)

sourceDir = '/scratch5/yiiyama/studies/monophoton/skim'

GroupSpec = collections.namedtuple('GroupSpec', ['title', 'samples', 'color'])

class VariableDef(object):
    def __init__(self, title, unit, expr, cut, binning, overflow = False):
        self.title = title
        self.unit = unit
        self.expr = expr
        self.cut = cut
        self.binning = binning
        self.overflow = overflow


region = sys.argv[1]

if region == 'monoph':
    defsel = 'monoph'
    obs = GroupSpec('Observed', ['sph-d3', 'sph-d4'], ROOT.kBlack)
    sigGroups = [GroupSpec('add5-1', ['add5-1'], ROOT.kGreen + 4)]
    bkgGroups = [
        ('minor', GroupSpec('t#bar{t}, Z', ['ttg', 'wlnu', 'dy-50'], ROOT.TColor.GetColor(0x55, 0x44, 0xff))),
        ('g', GroupSpec('#gamma + jets', ['g-40', 'g-100', 'g-200', 'g-400', 'g-600'], ROOT.TColor.GetColor(0xff, 0xaa, 0xcc))),
        ('qcd', GroupSpec('QCD', ['qcd-200', 'qcd-300', 'qcd-500', 'qcd-700', 'qcd-1000'], ROOT.TColor.GetColor(0xff, 0x44, 0x55))),
        ('hfake', GroupSpec('Hadronic fakes', [('sph-d3', 'hfake'), ('sph-d4', 'hfake')], ROOT.TColor.GetColor(0xbb, 0xaa, 0xff))),
        ('wg', GroupSpec('W#rightarrowl#nu+#gamma', ['wg'], ROOT.TColor.GetColor(0x99, 0xee, 0xff))),
        ('efake', GroupSpec('Electron fakes', [('sph-d3', 'efake'), ('sph-d4', 'efake')], ROOT.TColor.GetColor(0xff, 0xee, 0x99))),
        ('znunu', GroupSpec('Z#rightarrow#nu#nu+#gamma', ['znng'], ROOT.TColor.GetColor(0x99, 0xff, 0xaa)))
    ]
    
    variables = {
        'met': VariableDef('E_{T}^{miss}', 'GeV', 't1Met.met', '', [40. + 10. * x for x in range(12)] + [160. + 40. * x for x in range(4)] + [320., 400., 500.], overflow = True),
        'phoPt': VariableDef('p_{T}^{#gamma}', 'GeV', 'photons.pt[0]', '', [170. + 10. * x for x in range(13)] + [300. + 40. * x for x in range(6)], overflow = True),
        'phoPtHighMet': VariableDef('p_{T}^{#gamma}', 'GeV', 'photons.pt[0]', 't1Met.met > 100.', [170. + 10. * x for x in range(13)] + [300. + 40. * x for x in range(6)], overflow = True),
        'phoEta': VariableDef('#eta^{#gamma}', '', 'photons.eta[0]', '', (20, -1.5, 1.5)),
        'phoPhi': VariableDef('#phi^{#gamma}', '', 'photons.phi[0]', '', (20, -math.pi, math.pi)),
        'dPhiPhoMet': VariableDef('#Delta#phi(#gamma, E_{T}^{miss})', '', 'TVector2::Phi_mpi_pi(photons.phi[0] - t1Met.phi)', 't1Met.met > 40.', (20, -math.pi, math.pi)),
        'dPhiPhoMetHighMet': VariableDef('#Delta#phi(#gamma, E_{T}^{miss})', '', 'TVector2::Phi_mpi_pi(photons.phi[0] - t1Met.phi)', 't1Met.met > 100.', (20, -math.pi, math.pi)),
        'metPhiHighMet': VariableDef('#phi(E_{T}^{miss})', '', 't1Met.phi', 't1Met.met > 100.', (20, -math.pi, math.pi)),
        'njets': VariableDef('N_{jet}', '', 'jets.size', '', (10, 0., 10.))
    }

elif region == 'dimu':
    defsel = 'dimu'
    obs = GroupSpec('Observed', ['smu-d3', 'smu-d4'], ROOT.kBlack)
    bkgGroups = [
        ('ttg', GroupSpec('t#bar{t}#gamma', ['ttg'], ROOT.TColor.GetColor(0x55, 0x44, 0xff))),
        ('zg', GroupSpec('Z#rightarrowll+#gamma', ['zg'], ROOT.TColor.GetColor(0x99, 0xff, 0xaa)))
    ]

    mass = 'TMath::Sqrt(2. * muons.pt[0] * muons.pt[1] * (TMath::CosH(muons.eta[0] - muons.eta[1]) - TMath::Cos(muons.phi[0] - muons.phi[1])))'
    cut = mass + ' > 50.'

    dR2_00 = 'TMath::Power(photons.eta[0] - muons.eta[0], 2.) + TMath::Power(TVector2::Phi_mpi_pi(photons.phi[0] - muons.phi[0]), 2.)'
    dR2_01 = 'TMath::Power(photons.eta[0] - muons.eta[1], 2.) + TMath::Power(TVector2::Phi_mpi_pi(photons.phi[0] - muons.phi[1]), 2.)'
    
    variables = {
        'met': VariableDef('E_{T}^{miss}', 'GeV', 't1Met.met', cut, [40. + 10. * x for x in range(12)] + [160. + 40. * x for x in range(3)]),
        'phoPt': VariableDef('p_{T}^{#gamma}', 'GeV', 'photons.pt[0]', cut, [80. + 10. * x for x in range(22)] + [300. + 40. * x for x in range(6)]),
        'phoEta': VariableDef('#eta^{#gamma}', '', 'photons.eta[0]', cut, (20, -1.5, 1.5)),
        'phoPhi': VariableDef('#phi^{#gamma}', '', 'photons.phi[0]', cut, (20, -math.pi, math.pi)),
        'dPhiPhoMet': VariableDef('#Delta#phi(#gamma, E_{T}^{miss})', '', 'TVector2::Phi_mpi_pi(photons.phi[0] - t1Met.phi)', cut, (20, -math.pi, math.pi)),
        'dimumass': VariableDef('M_{#mu#mu}', 'GeV', mass, cut, (30, 50., 200.)),
        'dRPhoMu': VariableDef('#DeltaR(#gamma, #mu)_{min}', '', 'TMath::Sqrt(TMath::Min(%s, %s))' % (dR2_00, dR2_01), '', (20, 0., 4.)),
        'njets': VariableDef('N_{jet}', '', 'jets.size', cut, (10, 0., 10.))
    }

elif region == 'monomu':
    defsel = 'monomu'
    obs = GroupSpec('Observed', ['smu-d3', 'smu-d4'], ROOT.kBlack)
    bkgGroups = [
        ('wg', GroupSpec('W#gamma', ['wg'], ROOT.TColor.GetColor(0x99, 0xee, 0xff))),
        ('ttg', GroupSpec('t#bar{t}#gamma', ['ttg'], ROOT.TColor.GetColor(0x55, 0x44, 0xff))),
        ('zg', GroupSpec('Z#rightarrowll+#gamma', ['zg'], ROOT.TColor.GetColor(0x99, 0xff, 0xaa)))
    ]
    
    variables = {
        'met': VariableDef('E_{T}^{miss}', 'GeV', 't1Met.met', '', [40. + 10. * x for x in range(12)] + [160. + 40. * x for x in range(3)]),
        'mt': VariableDef('M_{T}', 'GeV', 'TMath::Sqrt(2. * t1Met.met * muons.pt[0] * (1. - TMath::Cos(TVector2::Phi_mpi_pi(t1Met.phi - muons.phi[0]))))', '', [0. + 10. * x for x in range(16)] + [160. + 40. * x for x in range(3)]),
        'phoPt': VariableDef('p_{T}^{#gamma}', 'GeV', 'photons.pt[0]', '', [60.] + [80. + 10. * x for x in range(22)] + [300. + 40. * x for x in range(6)]),
        'phoEta': VariableDef('#eta^{#gamma}', '', 'photons.eta[0]', '', (20, -1.5, 1.5)),
        'phoPhi': VariableDef('#phi^{#gamma}', '', 'photons.phi[0]', '', (20, -math.pi, math.pi)),
        'dPhiPhoMet': VariableDef('#Delta#phi(#gamma, E_{T}^{miss})', '', 'TVector2::Phi_mpi_pi(photons.phi[0] - t1Met.phi)', '', (20, -math.pi, math.pi)),
        'dRPhoMu': VariableDef('#DeltaR(#gamma, #mu)', '', 'TMath::Sqrt(TMath::Power(photons.eta[0] - muons.eta[0], 2.) + TMath::Power(TVector2::Phi_mpi_pi(photons.phi[0] - muons.phi[0]), 2.))', '', (20, 0., 4.)),
        'njets': VariableDef('N_{jet}', '', 'jets.size', '', (10, 0., 10.))
    }

elif region == 'diel':
    defsel = 'diel'
    obs = GroupSpec('Observed', ['sel-d3', 'sel-d4'], ROOT.kBlack)
    bkgGroups = [
        ('ttg', GroupSpec('t#bar{t}#gamma', ['ttg'], ROOT.TColor.GetColor(0x55, 0x44, 0xff))),
        ('zg', GroupSpec('Z#rightarrowll+#gamma', ['zg'], ROOT.TColor.GetColor(0x99, 0xff, 0xaa)))
    ]

    mass = 'TMath::Sqrt(2. * electrons.pt[0] * electrons.pt[1] * (TMath::CosH(electrons.eta[0] - electrons.eta[1]) - TMath::Cos(electrons.phi[0] - electrons.phi[1])))'
    cut = mass + ' > 50.'

    dR2_00 = 'TMath::Power(photons.eta[0] - electrons.eta[0], 2.) + TMath::Power(TVector2::Phi_mpi_pi(photons.phi[0] - electrons.phi[0]), 2.)'
    dR2_01 = 'TMath::Power(photons.eta[0] - electrons.eta[1], 2.) + TMath::Power(TVector2::Phi_mpi_pi(photons.phi[0] - electrons.phi[1]), 2.)'
    
    variables = {
        'met': VariableDef('E_{T}^{miss}', 'GeV', 't1Met.met', cut, [40. + 10. * x for x in range(12)] + [160. + 40. * x for x in range(3)]),
        'phoPt': VariableDef('p_{T}^{#gamma}', 'GeV', 'photons.pt[0]', cut, [80. + 10. * x for x in range(22)] + [300. + 40. * x for x in range(6)]),
        'phoEta': VariableDef('#eta^{#gamma}', '', 'photons.eta[0]', cut, (20, -1.5, 1.5)),
        'phoPhi': VariableDef('#phi^{#gamma}', '', 'photons.phi[0]', cut, (20, -math.pi, math.pi)),
        'dPhiPhoMet': VariableDef('#Delta#phi(#gamma, E_{T}^{miss})', '', 'TVector2::Phi_mpi_pi(photons.phi[0] - t1Met.phi)', cut, (20, -math.pi, math.pi)),
        'dielmass': VariableDef('M_{ee}', 'GeV', mass, cut, (30, 50., 200.)),
        'dRPhoEl': VariableDef('#DeltaR(#gamma, e)_{min}', '', 'TMath::Sqrt(TMath::Min(%s, %s))' % (dR2_00, dR2_01), '', (20, 0., 4.)),
        'njets': VariableDef('N_{jet}', '', 'jets.size', cut, (10, 0., 10.)),
    }

elif region == 'monoel':
    defsel = 'monoel'
    obs = GroupSpec('Observed', ['sel-d3', 'sel-d4'], ROOT.kBlack)
    bkgGroups = [
        ('wg', GroupSpec('W#gamma', ['wg'], ROOT.TColor.GetColor(0x99, 0xee, 0xff))),
        ('ttg', GroupSpec('t#bar{t}#gamma', ['ttg'], ROOT.TColor.GetColor(0x55, 0x44, 0xff))),
        ('zg', GroupSpec('Z#rightarrowll+#gamma', ['zg'], ROOT.TColor.GetColor(0x99, 0xff, 0xaa))),
        ('eefake', GroupSpec('Electron fakes', [('sel-d3', 'eefake'), ('sel-d4', 'eefake')], ROOT.TColor.GetColor(0xff, 0xee, 0x99)))
    ]
    
    variables = {
        'met': VariableDef('E_{T}^{miss}', 'GeV', 't1Met.met', '', [40. + 10. * x for x in range(12)] + [160. + 40. * x for x in range(3)]),
        'mt': VariableDef('M_{T}', 'GeV', 'TMath::Sqrt(2. * t1Met.met * electrons.pt[0] * (1. - TMath::Cos(TVector2::Phi_mpi_pi(t1Met.phi - electrons.phi[0]))))', '', [0. + 10. * x for x in range(16)] + [160. + 40. * x for x in range(3)]),
        'phoPt': VariableDef('p_{T}^{#gamma}', 'GeV', 'photons.pt[0]', '', [60.] + [80. + 10. * x for x in range(22)] + [300. + 40. * x for x in range(6)]),
        'phoEta': VariableDef('#eta^{#gamma}', '', 'photons.eta[0]', '', (20, -1.5, 1.5)),
        'phoPhi': VariableDef('#phi^{#gamma}', '', 'photons.phi[0]', '', (20, -math.pi, math.pi)),
        'dPhiPhoMet': VariableDef('#Delta#phi(#gamma, E_{T}^{miss})', '', 'TVector2::Phi_mpi_pi(photons.phi[0] - t1Met.phi)', '', (20, -math.pi, math.pi)),
        'dRPhoEl': VariableDef('#DeltaR(#gamma, #mu)', '', 'TMath::Sqrt(TMath::Power(photons.eta[0] - electrons.eta[0], 2.) + TMath::Power(TVector2::Phi_mpi_pi(photons.phi[0] - electrons.phi[0]), 2.))', '', (20, 0., 4.)),
        'njets': VariableDef('N_{jet}', '', 'jets.size', '', (10, 0., 10.))
    }

elif region == 'elmu':
    defsel = 'elmu'
    obs = GroupSpec('Observed', ['smu-d3', 'smu-d4'], ROOT.kBlack)
    bkgGroups = [
        ('ttg', GroupSpec('t#bar{t}#gamma', ['ttg'], ROOT.TColor.GetColor(0x55, 0x44, 0xff))),
        ('zg', GroupSpec('Z#rightarrowll+#gamma', ['zg'], ROOT.TColor.GetColor(0x99, 0xff, 0xaa)))
    ]
    
    variables = {
        'met': VariableDef('E_{T}^{miss}', 'GeV', 't1Met.met', '', [40. + 10. * x for x in range(12)] + [160. + 40. * x for x in range(3)]),
        'phoPt': VariableDef('p_{T}^{#gamma}', 'GeV', 'photons.pt[0]', '', [80. + 10. * x for x in range(22)] + [300. + 40. * x for x in range(6)]),
        'phoEta': VariableDef('#eta^{#gamma}', '', 'photons.eta[0]', '', (20, -1.5, 1.5)),
        'phoPhi': VariableDef('#phi^{#gamma}', '', 'photons.phi[0]', '', (20, -math.pi, math.pi)),
        'dPhiPhoMet': VariableDef('#Delta#phi(#gamma, E_{T}^{miss})', '', 'TVector2::Phi_mpi_pi(photons.phi[0] - t1Met.phi)', '', (20, -math.pi, math.pi)),
        'njets': VariableDef('N_{jet}', '', 'jets.size', '', (10, 0., 10.))
    }

else:
    print 'Unknown region', region
    sys.exit(0)

sensitive = {'monoph': ['met']}
blind = 5

lumi = sum([allsamples[s].lumi for s in obs.samples])

canvas = DataMCCanvas(lumi = lumi)
simpleCanvas = SimpleCanvas(lumi = lumi, sim = True)

def getHist(sampledef, selection, varname, vardef, isSensitive = False):
    source = ROOT.TFile.Open(sourceDir + '/' + sampledef.name + '_' + selection + '.root')
    tree = source.Get('events')

    if type(vardef.binning) is list:
        nbins = len(vardef.binning) - 1
        binning = list(vardef.binning)
    elif type(vardef.binning) is tuple:
        nbins = vardef.binning[0]
        binning = [vardef.binning[1] + (vardef.binning[2] - vardef.binning[1]) / nbins * i for i in range(nbins + 1)]

    arr = array.array('d', binning)

    hist = ROOT.TH1D(varname + '-' + sampledef.name, '', nbins, arr)

    cut = vardef.cut
    if isSensitive and blind != 1:
        if cut:
            cut += ' && event % {blind} == 0'.format(blind = blind)
        else:
            cut = ' event % {blind} == 0'.format(blind = blind)

    if cut:
        weightexpr = 'weight * (%s)' % cut
    else:
        weightexpr = 'weight'

    hist.Sumw2()
    if sampledef.data:
        tree.Draw(vardef.expr + '>>' + varname + '-' + sampledef.name, weightexpr, 'goff')
    else:
        tree.Draw(vardef.expr + '>>' + varname + '-' + sampledef.name, str(lumi) + ' * ' + weightexpr, 'goff')

    if vardef.overflow:
        binning += [binning[-1] + (binning[1] - binning[0])]
        arr = array.array('d', binning)
        hist.SetBins(len(binning) - 1, arr)

    hist.SetDirectory(0)
    for iX in range(1, nbins + 1):
        cont = hist.GetBinContent(iX)
        err = hist.GetBinError(iX)
        w = hist.GetXaxis().GetBinWidth(iX)
        if vardef.unit:
            hist.SetBinContent(iX, cont / w)
            hist.SetBinError(iX, err / w)
        else:
            if iX == 1:
                wnorm = w
            hist.SetBinContent(iX, cont / (w / wnorm))
            hist.SetBinError(iX, err / (w / wnorm))

    xtitle = vardef.title
    if vardef.unit:
        xtitle += '(%s)' % vardef.unit

    ytitle = 'Events'
    if hist.GetXaxis().GetBinWidth(1) != 1.:
        ytitle += ' / '
        if vardef.unit:
            ytitle += vardef.unit
        else:
            ytitle += '%.2f' % hist.GetXaxis().GetBinWidth(1)

    hist.GetXaxis().SetTitle(xtitle)
    hist.GetYaxis().SetTitle(ytitle)

    return hist

def highMetYield(hist):
    s = 0.
    iBin = hist.GetXaxis().FindFixBin(240.)
    while iBin < hist.GetNbinsX():
        s += hist.GetBinContent(iBin) * hist.GetXaxis().GetBinWidth(iBin)
        iBin += 1

    s += hist.GetBinContent(hist.GetNbinsX())
    return s

for varname, vardef in variables.items():
    canvas.Clear(full = True)
    canvas.legend.setPosition(0.6, 0.6, 0.92, 0.92)

    isSensitive = region in sensitive and varname in sensitive[region]

    if varname == 'met':
        counts = {}

    for gName, group in bkgGroups:
        idx = -1
        for sName in group.samples:
            if type(sName) is tuple:
                selection = sName[1]
                sName = sName[0]
            else:
                selection = defsel

            hist = getHist(allsamples[sName], selection, varname, vardef)
#            simpleCanvas.Clear()
#            simpleCanvas.cd()
#            hist.Draw()
#            simpleCanvas.printWeb('monophoton', sName)

            for iX in range(1, hist.GetNbinsX() + 1):
                if hist.GetBinContent(iX) < 0.:
                    hist.SetBinContent(iX, 0.)

            if varname == 'met':
                if gName == 'efake':
                    counts['efake'] = highMetYield(hist)
                elif gName == 'hfake':
                    counts['hfake'] = highMetYield(hist)
                else:
                    if 'mc' not in counts:
                        counts['mc'] = 0.
                    counts['mc'] += highMetYield(hist)

            if isSensitive and blind != 1:
                hist.Scale(1. / blind)

            idx = canvas.addStacked(hist, title = group.title, color = group.color, idx = idx)
            
    if isSensitive:
        for sGroup in sigGroups:
            idx = -1
            for sName in sGroup.samples:
                hist = getHist(allsamples[sName], defsel, varname, vardef)
                counts[sName] = highMetYield(hist)
                if blind != 1:
                    hist.Scale(1. / blind)

                idx = canvas.addSignal(hist, title = sGroup.title, color = sGroup.color, idx = idx)

    if varname == 'met':
        print counts

    for sName in obs.samples:
        hist = getHist(allsamples[sName], defsel, varname, vardef, isSensitive)
        canvas.addObs(hist, title = obs.title)

    canvas.xtitle = canvas.obsHistogram().GetXaxis().GetTitle()
    canvas.ytitle = canvas.obsHistogram().GetYaxis().GetTitle()

    canvas.printWeb('monophoton_' + region, varname)
    canvas.printWeb('monophoton_' + region, varname + '-linear', logy = False)
