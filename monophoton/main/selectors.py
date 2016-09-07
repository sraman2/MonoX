import sys
import os
import array
needHelp = False
for opt in ['-h', '--help']:
    if opt in sys.argv:
        needHelp = True
        sys.argv.remove(opt)

import ROOT

thisdir = os.path.dirname(os.path.realpath(__file__))
basedir = os.path.dirname(thisdir)

if basedir not in sys.path:
    sys.path.append(basedir)

import config

ROOT.gSystem.Load(config.libsimpletree)
ROOT.gSystem.AddIncludePath('-I' + config.dataformats + '/interface')

#ROOT.gROOT.LoadMacro(thisdir + '/jer.cc+')
ROOT.gROOT.LoadMacro(thisdir + '/operators.cc+')
ROOT.gROOT.LoadMacro(thisdir + '/selectors.cc+')

photonFullSelection = [
    'HOverE',
    'Sieie',
    'CHIso',
    'CHWorstIso',
    'NHIso',
    'PhIso',
    'EVeto',
    'MIP49',
    'Time',
    'SieieNonzero',
    'SipipNonzero',
#    'E2E995',
    'NoisyRegion'
]

puWeightSource = ROOT.TFile.Open(basedir + '/data/pileup.root')
puWeight = puWeightSource.Get('puweight')

# photonSFSource = ROOT.TFile.Open(basedir + '/data/photon_id_scalefactor.root')
photonSFSource = ROOT.TFile.Open(basedir + '/data/photon_id_sf16.root')
photonSF = photonSFSource.Get('EGamma_SF2D')

# eventFiltersPath = '/scratch5/yiiyama/eventlists'
eventFiltersPath = '/badpath/bad'
if os.path.exists(eventFiltersPath):
    eventLists = os.listdir(eventFiltersPath)
else:
    eventLists = []
print eventLists

hadproxySource = ROOT.TFile.Open(basedir + '/data/hadronTFactor.root')
hadproxyWeight = hadproxySource.Get('tfactWorst')
hadproxyupWeight = hadproxySource.Get('tfactWorstUp')
hadproxydownWeight = hadproxySource.Get('tfactWorstDown')
hadproxyPurityUpWeight = hadproxySource.Get('tfactWorstPurityUp')
hadproxyPurityDownWeight = hadproxySource.Get('tfactWorstPurityDown')

eleproxySource = ROOT.TFile.Open(basedir + '/data/efake_data_pt.root')
eleproxyWeight = eleproxySource.Get('frate')

trigCorrFormula = '1.025 - 0.0001163 * x'
trigCorrUpFormula = '1.025 - 0.0001163 * x'
trigCorrDownFormula = '1.025 - 0.0001163 * x'

gjSmearingFormula = 'TMath::Landau(x, [0], [1])'
gjSmearingParams = (-0.7314, 0.5095) # measured in gjets/smearfit.py

muonTightSFSource = ROOT.TFile.Open(basedir + '/data/scaleFactor_muon_tightid_12p9.root')
muonTightSF = muonTightSFSource.Get('scaleFactor_muon_tightid_Exp')
muonLooseSFSource = ROOT.TFile.Open(basedir + '/data/scaleFactor_muon_looseid_12p9.root')
muonLooseSF = muonLooseSFSource.Get('scaleFactor_muon_looseid_Exp')
muonTrigSFSource = ROOT.TFile.Open(basedir + '/data/muonTrigSF.root')
muonTrigSF = muonTrigSFSource.Get('mutrksfptg10')

electronTightSFSource = ROOT.TFile.Open(basedir + '/data/scaleFactor_electron_tightid_12p9.root')
electronTightSF = electronTightSFSource.Get('scaleFactor_electron_tightid_Exp')
electronVetoSFSource = ROOT.TFile.Open(basedir + '/data/scaleFactor_electron_vetoid_12p9.root')
electronVetoSF = electronVetoSFSource.Get('scaleFactor_electron_vetoid_Exp')

##############################################################
# Argument "selector" in all functions below can either be an
# actual Selector object or a name for the selector.
##############################################################

def monophotonBase(sample, selector):
    """
    Monophoton candidate-like selection (high-pT photon, lepton veto, dphi(photon, MET) and dphi(jet, MET)).
    Base for other selectors.
    """

    if type(selector) is str: # this is a name for the selector
        selector = ROOT.EventSelector(selector)

    operators = []

    if sample.data:
        operators.append(('HLTFilter', 'HLT_Photon165_HE10'))

    operators += [
        'MetFilters',
        'PhotonSelection',
        'MuonVeto',
        'ElectronVeto',
        'TauVeto',
        'JetCleaning',
        'CopyMet'
    ]

    if not sample.data:
        operators.append('MetVariations')
        
    operators += [
        'PhotonMetDPhi',
        'JetMetDPhi',
        'PhotonJetDPhi',
        'HighMet'
    ]

    for op in operators:
        if type(op) is tuple:
            selector.addOperator(getattr(ROOT, op[0])(*op[1:]))
        else:
            selector.addOperator(getattr(ROOT, op)())

    if not sample.data:
        metVar = selector.findOperator('MetVariations')
        jetClean = selector.findOperator('JetCleaning')
        metVar.setPhotonSelection(selector.findOperator('PhotonSelection'))
#        metVar.setJetCleaning(jetClean)

#        jetClean.setJetResolution(basedir + '/data/Summer15_25nsV6_MC_PtResolution_AK4PFchs.txt')

        photonDPhi = selector.findOperator('PhotonMetDPhi')
        photonDPhi.setMetVariations(metVar)
        
        jetDPhi = selector.findOperator('JetMetDPhi')
        jetDPhi.setMetVariations(metVar)
#        jetDPhi.setJetCleaning(jetClean)

        selector.findOperator('PhotonJetDPhi').setMetVariations(metVar)

        selector.addOperator(ROOT.ConstantWeight(sample.crosssection / sample.sumw, 'crosssection'))
        selector.addOperator(ROOT.PUWeight(puWeight))

        trigCorr = ROOT.TriggerEfficiency()
        trigCorr.setMinPt(300.)
        trigCorr.setFormula(trigCorrFormula)
        trigCorr.setUpFormula(trigCorrUpFormula)
        trigCorr.setDownFormula(trigCorrDownFormula)
        selector.addOperator(trigCorr)

    selector.findOperator('TauVeto').setIgnoreDecision(True)
    selector.findOperator('JetCleaning').setCleanAgainst(ROOT.JetCleaning.kTaus, False)
    selector.findOperator('PhotonMetDPhi').setIgnoreDecision(True)
    selector.findOperator('JetMetDPhi').setIgnoreDecision(True)
    selector.findOperator('HighMet').setIgnoreDecision(True)

    return selector

def candidate(sample, selector):
    """
    Full monophoton selection.
    """

    selector = monophotonBase(sample, selector)

    if sample.data:
        for eventList in eventLists:
            selector.findOperator('MetFilters').setEventList(str(eventFiltersPath + '/' + eventList), 1)
    else:
        idsf = ROOT.IDSFWeight(ROOT.IDSFWeight.kPhoton, 'photonSF')
        idsf.addFactor(photonSF)
        idsf.setVariable(ROOT.IDSFWeight.kEta, ROOT.IDSFWeight.kPt)
        selector.addOperator(idsf)
        # selector.addOperator(ROOT.ConstantWeight(1.01, 'extraSF'))
        if 'amcatnlo' in sample.fullname or 'madgraph' in sample.fullname: # ouh la la..
            selector.addOperator(ROOT.NNPDFVariation())

    photonSel = selector.findOperator('PhotonSelection')

    for sel in photonFullSelection:
        photonSel.addSelection(True, getattr(ROOT.PhotonSelection, sel))

    return selector

def signalRaw(sample, selector):
    """
    Ignore decisions of all cuts to compare shapes for different simulations.
    """

    selector = candidate(sample, selector)

    cuts = ['MetFilters', 'PhotonSelection', 'ElectronVeto', 'MuonVeto', 'TauVeto', 'PhotonMetDPhi', 'JetMetDPhi', 'HighMet']
    for cut in cuts:
        # print cut
        selector.findOperator(cut).setIgnoreDecision(True)

    return selector

def eleProxy(sample, selector):
    """
    Candidate-like but with inverted electron veto
    """

    selector = monophotonBase(sample, selector)

    bin = eleproxyWeight.FindFixBin(175.)
    if bin > eleproxyWeight.GetNbinsX():
        bin = eleproxyWeight.GetNbinsX()

    w = eleproxyWeight.GetBinContent(bin)

    weight = ROOT.ConstantWeight(w, 'egfakerate')
    weight.setUncertaintyUp(eleproxyWeight.GetBinError(bin) / w)
    weight.setUncertaintyDown(eleproxyWeight.GetBinError(bin) / w)
    selector.addOperator(weight)

    photonSel = selector.findOperator('PhotonSelection')

    sels = list(photonFullSelection)
    sels.remove('EVeto')

    for sel in sels:
        photonSel.addSelection(True, getattr(ROOT.PhotonSelection, sel))
        photonSel.addVeto(True, getattr(ROOT.PhotonSelection, sel))

    photonSel.addSelection(False, ROOT.PhotonSelection.EVeto)
    photonSel.addSelection(False, ROOT.PhotonSelection.CSafeVeto)
    photonSel.addVeto(True, ROOT.PhotonSelection.EVeto)

    return selector

def lowmt(sample, selector):
    """
    Wenu-enriched control region.
    """

    selector = monophotonBase(sample, selector)

    if not sample.data:
        idsf = ROOT.IDSFWeight(ROOT.IDSFWeight.kPhoton, 'photonSF')
        idsf.addFactor(photonSF)
        idsf.setVariable(ROOT.IDSFWeight.kEta, ROOT.IDSFWeight.kPt)
        selector.addOperator(idsf)
        # selector.addOperator(ROOT.ConstantWeight(1.01, 'extraSF'))
        if 'amcatnlo' in sample.fullname or 'madgraph' in sample.fullname: # ouh la la..
            selector.addOperator(ROOT.NNPDFVariation())

    photonSel = selector.findOperator('PhotonSelection')

    for sel in photonFullSelection:
        photonSel.addSelection(True, getattr(ROOT.PhotonSelection, sel))

    photonSel.setMaxPt(400.)

    mtCut = ROOT.MtRange()
    mtCut.setRange(50., 150.)
    selector.addOperator(mtCut)

    dphi = selector.findOperator('PhotonMetDPhi')
    dphi.invert(True)

    return selector

def lowmtEleProxy(sample, selector):
    """
    Wenu-enriched control region.
    """

    selector = eleProxy(sample, selector)

    photonSel = selector.findOperator('PhotonSelection')
    photonSel.setMaxPt(400.)

    mtCut = ROOT.MtRange()
    mtCut.setRange(50., 150.)
    selector.addOperator(mtCut)

    return selector

def purityBase(sample, selector):
    """
    Base selector for EM+Jet control region.
    """

    if type(selector) is str: # this is a name for the selector
        selector = ROOT.EventSelector(selector)

    operators = []

    if sample.data:
        operators.append(('HLTFilter', 'HLT_Photon165_HE10'))

    operators += [
        'MetFilters',
        'PhotonSelection',
        'MuonVeto',
        'ElectronVeto',
        'TauVeto',
        'JetCleaning',
        'HighPtJetSelection',
        'CopyMet'
    ]

    operators += [
        'JetMetDPhi',
        'PhotonMetDPhi'
    ]

    for op in operators:
        if type(op) is tuple:
            selector.addOperator(getattr(ROOT, op[0])(*op[1:]))
        else:
            selector.addOperator(getattr(ROOT, op)())

    if not sample.data:
        selector.addOperator(ROOT.ConstantWeight(sample.crosssection / sample.sumw, 'crosssection'))
        selector.addOperator(ROOT.PUWeight(puWeight))

    selector.findOperator('PhotonSelection').setMinPt(100.)
    selector.findOperator('TauVeto').setIgnoreDecision(True)
    selector.findOperator('JetCleaning').setCleanAgainst(ROOT.JetCleaning.kTaus, False)
    selector.findOperator('HighPtJetSelection').setJetPtCut(100.)
    selector.findOperator('JetMetDPhi').setIgnoreDecision(True)
    selector.findOperator('PhotonMetDPhi').setIgnoreDecision(True)

    return selector

def purity(sample, selector):
    """
    EM Object is baseline photon, used for efficiency and SF measurements as well.
    """

    selector = purityBase(sample, selector)

    photonSel = selector.findOperator('PhotonSelection')

    sels = []
    sels.append('Sieie15')
    # sels.append('CHIso11')

    for sel in sels:
        photonSel.addSelection(True, getattr(ROOT.PhotonSelection, sel))

    return selector

def purityUp(sample, selector):
    """
    EM Object is true photon like, but with tightened NHIso and PhIso requirements and inverted sieie and CHIso requirements.
    """

    selector = purityBase(sample, selector)

    photonSel = selector.findOperator('PhotonSelection')

    sels = list(photonFullSelection)
    sels.remove('Sieie')
    sels.remove('CHIso')
    sels.remove('CHWorstIso')
    sels.append('Sieie15')
    sels.append('NHIsoTight')
    sels.append('PhIsoTight')
    sels.append('CHWorstIso11')

    for sel in sels:
        photonSel.addSelection(True, getattr(ROOT.PhotonSelection, sel))
        photonSel.addVeto(True, getattr(ROOT.PhotonSelection, sel))

    photonSel.addSelection(False, ROOT.PhotonSelection.Sieie12, ROOT.PhotonSelection.CHWorstIso)
    photonSel.addVeto(True, ROOT.PhotonSelection.Sieie12)
    photonSel.addVeto(True, ROOT.PhotonSelection.CHWorstIso)

    return selector

def purityDown(sample, selector):
    """
    EM Object is true photon like, but with inverted NHIso and PhIso requirements and loosened sieie and CHIso requirements.
    """

    selector = purityBase(sample, selector)

    photonSel = selector.findOperator('PhotonSelection')

    sels = list(photonFullSelection)
    sels.remove('NHIso')
    sels.remove('PhIso')
    sels.remove('Sieie')
    sels.remove('CHIso')
    sels.remove('CHWorstIso')
    sels.append('Sieie15')
    sels.append('CHWorstIso11')
    sels.append('NHIso11')
    sels.append('PhIso3')

    for sel in sels:
        photonSel.addSelection(True, getattr(ROOT.PhotonSelection, sel))
        photonSel.addVeto(True, getattr(ROOT.PhotonSelection, sel))

    photonSel.addSelection(False, ROOT.PhotonSelection.NHIso, ROOT.PhotonSelection.PhIso)
    photonSel.addVeto(True, ROOT.PhotonSelection.NHIso)
    photonSel.addVeto(True, ROOT.PhotonSelection.PhIso)

    return selector

def hadProxy(sample, selector):
    """
    Candidate-like but with inverted sieie or CHIso.
    """

    if type(selector) is str:
        selector = monophotonBase(sample, selector)

    weight = ROOT.PhotonPtWeight(hadproxyWeight, 'hadProxyWeight')
    weight.setPhotonType(ROOT.PhotonPtWeight.kReco)
    weight.addVariation('purityUp', hadproxyPurityUpWeight)
    weight.addVariation('purityDown', hadproxyPurityDownWeight)
    selector.addOperator(weight)

    photonSel = selector.findOperator('PhotonSelection')

    sels = list(photonFullSelection)
    sels.remove('Sieie')
    sels.remove('CHIso')
    sels.remove('CHWorstIso')
    sels.append('Sieie15')
    sels.append('CHWorstIso11')

    for sel in sels:
        photonSel.addSelection(True, getattr(ROOT.PhotonSelection, sel))
        photonSel.addVeto(True, getattr(ROOT.PhotonSelection, sel))

    photonSel.addSelection(False, ROOT.PhotonSelection.Sieie12, ROOT.PhotonSelection.CHWorstIso)
    photonSel.addVeto(True, ROOT.PhotonSelection.Sieie12)
    photonSel.addVeto(True, ROOT.PhotonSelection.CHWorstIso)

    return selector

def hadProxyUp(sample, selector):
    """
    Candidate-like with tight NHIso and PhIso, with inverted sieie or CHIso.
    """

    selector = monophotonBase(sample, selector)

    weight = ROOT.PhotonPtWeight(hadproxyupWeight)
    weight.setPhotonType(ROOT.PhotonPtWeight.kReco)
    selector.addOperator(weight)

    photonSel = selector.findOperator('PhotonSelection')

    sels = list(photonFullSelection)
    sels.remove('Sieie')
    sels.remove('CHIso')
    sels.remove('CHWorstIso')
    sels.append('NHIsoTight')
    sels.append('PhIsoTight')
    sels.append('Sieie15')
    sels.append('CHWorstIso11')

    for sel in sels:
        photonSel.addSelection(True, getattr(ROOT.PhotonSelection, sel))
        photonSel.addVeto(True, getattr(ROOT.PhotonSelection, sel))

    photonSel.addSelection(False, ROOT.PhotonSelection.Sieie12, ROOT.PhotonSelection.CHWorstIso)
    photonSel.addVeto(True, ROOT.PhotonSelection.Sieie12)
    photonSel.addVeto(True, ROOT.PhotonSelection.CHWorstIso)

    return selector

def hadProxyDown(sample, selector):
    """
    Candidate-like, but with loosened sieie + CHIso and inverted NHIso or PhIso.
    """

    selector = monophotonBase(sample, selector)

    weight = ROOT.PhotonPtWeight(hadproxydownWeight)
    weight.setPhotonType(ROOT.PhotonPtWeight.kReco)
    selector.addOperator(weight)

    photonSel = selector.findOperator('PhotonSelection')

    sels = list(photonFullSelection)
    sels.remove('Sieie')
    sels.remove('CHIso')
    sels.remove('CHWorstIso')
    sels.remove('NHIso')
    sels.remove('PhIso')
    sels.append('Sieie15')
    sels.append('CHWorstIso11')
    sels.append('NHIso11')
    sels.append('PhIso3')

    for sel in sels:
        photonSel.addSelection(True, getattr(ROOT.PhotonSelection, sel))
        photonSel.addVeto(True, getattr(ROOT.PhotonSelection, sel))

    photonSel.addSelection(False, ROOT.PhotonSelection.NHIso, ROOT.PhotonSelection.PhIso)
    photonSel.addVeto(True, ROOT.PhotonSelection.NHIso)
    photonSel.addVeto(True, ROOT.PhotonSelection.PhIso)

    return selector

def gjets(sample, selector):
    """
    Candidate-like, but with a high pT jet and inverted sieie and chIso on the photon.
    """
    
    selector = monophotonBase(sample, selector)
    
    selector.addOperator(ROOT.HighPtJetSelection())
    selector.findOperator('HighPtJetSelection').setJetPtCut(100.)
    
    photonSel = selector.findOperator('PhotonSelection')

    sels = list(photonFullSelection)
    sels.remove('Sieie')
    sels.remove('CHIso')
    sels.remove('CHWorstIso')
    sels.append('Sieie15')
    sels.append('CHWorstIso11')
    sels.append('CHIso11')

    for sel in sels:
        photonSel.addSelection(True, getattr(ROOT.PhotonSelection, sel))
        photonSel.addVeto(True, getattr(ROOT.PhotonSelection, sel))

    photonSel.addSelection(False, ROOT.PhotonSelection.Sieie12, ROOT.PhotonSelection.CHWorstIso)
    photonSel.addVeto(True, ROOT.PhotonSelection.Sieie12)
    photonSel.addVeto(True, ROOT.PhotonSelection.CHWorstIso)
    photonSel.addVeto(True, ROOT.PhotonSelection.CHIso)
    
    return selector

def gjSmeared(sample, name):
    """
    Candidate-like, with a smeared MET distribution.
    """

    selector = candidate(sample, ROOT.SmearingSelector(name))

    smearing = ROOT.TF1('smearing', gjSmearingFormula, 0., 40.)
    smearing.SetParameters(*gjSmearingParams) # measured in gjets/smearfit.py
    selector.setNSamples(1)
    selector.setFunction(smearing)

    return selector

def sampleDefiner(norm, inverts, removes, appends, CSCFilter = True):
    """
    Candidate-like, but with inverted MIP tag and CSC filter.
    """

    def normalized(sample, name):
        selector = ROOT.NormalizingSelector(name)
        selector.setNormalization(norm, 'photons.scRawPt[0] > 175. && t1Met.met > 170. && t1Met.photonDPhi > 2. && t1Met.minJetDPhi > 0.5')

        selector = monophotonBase(sample, selector)

        # 0->GlobalHalo16 tagger - not in st18 samples
        if not CSCFilter:
            selector.findOperator('MetFilters').setFilter(0, -1)

        if sample.data:
            for eventList in eventLists:
                if 'Halo' in eventList and CSCFilter is None:
                    selector.findOperator('MetFilters').setEventList(str(eventFiltersPath + '/' + eventList), 0)
                elif 'Halo' in eventList and not CSCFilter:
                    selector.findOperator('MetFilters').setEventList(str(eventFiltersPath + '/' + eventList), -1)
                else:
                    selector.findOperator('MetFilters').setEventList(str(eventFiltersPath + '/' + eventList), 1)

        photonSel = selector.findOperator('PhotonSelection')

        sels = list(photonFullSelection)

        for invert in inverts:
            if invert in sels:
                sels.remove(invert)
            photonSel.addSelection(False, getattr(ROOT.PhotonSelection, invert))

        for remove in removes:
            sels.remove(remove)

        for append in appends:
            sels.append(append)

        for sel in sels:
            photonSel.addSelection(True, getattr(ROOT.PhotonSelection, sel))

        return selector

    return normalized


def haloMIP(norm):
    """
    Wrapper to return the generator for the halo proxy sample normalized to norm.
    """

    inverts = [ 'MIP49' ]
    removes = [ 'Sieie' ]
    appends = [ 'Sieie15' ] 

    return sampleDefiner(norm, inverts, removes, appends, CSCFilter = None)

def haloCSC(norm):
    """
    Wrapper to return the generator for the halo proxy sample normalized to norm.
    """

    inverts = []
    removes = [ 'Sieie', 'MIP49' ]
    appends = [ 'Sieie15' ] 

    return sampleDefiner(norm, inverts, removes, appends, CSCFilter = False)

def haloSieie(norm):
    """
    Wrapper to return the generator for the halo proxy sample normalized to norm.
    """

    inverts = [ 'Sieie15' ]
    removes = [ 'Sieie', 'MIP49' ]
    appends = [] 

    return sampleDefiner(norm, inverts, removes, appends)

def spikeE2E9(norm):
    """
    Wrapper to return the generator for the spike proxy sample normalized to norm.
    """
    
    inverts = [ 'E2E995' ]
    removes = [ 'SieieNonzero', 'SipipNonzero']
    appends = [] 

    return sampleDefiner(norm, inverts, removes, appends)

def spikeSieie(norm):
    """
    Wrapper to return the generator for the spike proxy sample normalized to norm.
    """
    
    inverts = []
    removes = [ 'SipipNonzero', 'SieieNonzero' ]
    appends = [ 'Sieie05' ]

    return sampleDefiner(norm, inverts, removes, appends)

def spikeSipip(norm):
    """
    Wrapper to return the generator for the spike proxy sample normalized to norm.
    """
    
    inverts = []
    removes = [ 'SieieNonzero', 'SipipNonzero' ]
    appends = [ 'Sipip05' ]

    return sampleDefiner(norm, inverts, removes, appends)

def leptonBase(sample, selector):
    """
    Base for n-lepton + photon selection
    """

    if type(selector) is str: # this is a name for the selector
        selector = ROOT.EventSelector(selector)

    operators = [
        'MetFilters',
        'PhotonSelection',
        'LeptonSelection',
        'TauVeto',
        'JetCleaning',
        'LeptonRecoil',
        ]

    if not sample.data:
        operators.append('MetVariations')
    
    operators += [
        'PhotonMetDPhi',
        'JetMetDPhi',
        'HighMet'
    ]

    for op in operators:
        selector.addOperator(getattr(ROOT, op)())

    if not sample.data:
        metVar = selector.findOperator('MetVariations')
        jetClean = selector.findOperator('JetCleaning')
        metVar.setPhotonSelection(selector.findOperator('PhotonSelection'))
        
        photonDPhi = selector.findOperator('PhotonMetDPhi')
        photonDPhi.setMetVariations(metVar)
        
        jetDPhi = selector.findOperator('JetMetDPhi')
        jetDPhi.setMetVariations(metVar)

        selector.addOperator(ROOT.ConstantWeight(sample.crosssection / sample.sumw, 'crosssection'))
        selector.addOperator(ROOT.PUWeight(puWeight))

        idsf = ROOT.IDSFWeight(ROOT.IDSFWeight.kPhoton, 'photonSF')
        idsf.addFactor(photonSF)
        idsf.setVariable(ROOT.IDSFWeight.kEta, ROOT.IDSFWeight.kPt)
        selector.addOperator(idsf)
        # selector.addOperator(ROOT.ConstantWeight(1.01, 'extraSF'))
        if 'amcatnlo' in sample.fullname or 'madgraph' in sample.fullname: # ouh la la..
            selector.addOperator(ROOT.NNPDFVariation())

    photonSel = selector.findOperator('PhotonSelection')
    photonSel.setMinPt(30.)
    for sel in photonFullSelection:
        photonSel.addSelection(True, getattr(ROOT.PhotonSelection, sel))

    selector.findOperator('TauVeto').setIgnoreDecision(True)
    selector.findOperator('JetCleaning').setCleanAgainst(ROOT.JetCleaning.kTaus, False)
    selector.findOperator('PhotonMetDPhi').setIgnoreDecision(True)
    selector.findOperator('JetMetDPhi').setIgnoreDecision(True)
    selector.findOperator('HighMet').setIgnoreDecision(True)

    return selector

def electronBase(sample, selector):
    selector = leptonBase(sample, selector)
    selector.findOperator('LeptonRecoil').setCollection(ROOT.LeptonRecoil.kElectrons)
    if sample.data:
        selector.addOperator(ROOT.HLTFilter('HLT_Ele27_WPTight_Gsf'), 0)
    return selector

def muonBase(sample, selector):
    selector = leptonBase(sample, selector)
    selector.findOperator('LeptonRecoil').setCollection(ROOT.LeptonRecoil.kMuons)

    if sample.data:
        # for MC apply inefficiency depending on the number of muons
        selector.addOperator(ROOT.HLTFilter('HLT_IsoMu20_OR_HLT_IsoTkMu20'), 0)

    return selector

def dielectron(sample, selector):
    selector = electronBase(sample, selector)
    selector.findOperator('LeptonSelection').setN(2, 0)

    if not sample.data:
        idsf = ROOT.IDSFWeight(ROOT.IDSFWeight.kElectron, 'ElectronSF')
        idsf.addFactor(electronTightSF)
        idsf.addFactor(electronVetoSF)
        idsf.setNParticles(2)
        idsf.setVariable(ROOT.IDSFWeight.kAbsEta, ROOT.IDSFWeight.kPt)
        selector.addOperator(idsf)

    return selector

def monoelectron(sample, selector):
    selector = electronBase(sample, selector)
    selector.findOperator('LeptonSelection').setN(1, 0)

    if not sample.data:
        idsf = ROOT.IDSFWeight(ROOT.IDSFWeight.kElectron, 'ElectronSF')
        idsf.addFactor(electronTightSF)
        idsf.setVariable(ROOT.IDSFWeight.kAbsEta, ROOT.IDSFWeight.kPt)
        selector.addOperator(idsf)

    return selector

def monoelectronHadProxy(sample, selector):
    selector = electronBase(sample, selector)
    selector.findOperator('LeptonSelection').setN(1, 0)

    if not sample.data:
        idsf = ROOT.IDSFWeight(ROOT.IDSFWeight.kElectron, 'ElectronSF')
        idsf.addFactor(electronTightSF)
        idsf.setVariable(ROOT.IDSFWeight.kAbsEta, ROOT.IDSFWeight.kPt)
        selector.addOperator(idsf)

    selector = hadProxy(sample, selector)

    return selector

def dimuon(sample, selector):
    selector = muonBase(sample, selector)
    selector.findOperator('LeptonSelection').setN(0, 2)

    if not sample.data:
        idsf = ROOT.IDSFWeight(ROOT.IDSFWeight.kMuon, 'MuonSF')
        idsf.addFactor(muonTightSF)
        idsf.addFactor(muonLooseSF)
        idsf.setNParticles(2)
        idsf.setVariable(ROOT.IDSFWeight.kAbsEta, ROOT.IDSFWeight.kPt)
        selector.addOperator(idsf)

    return selector

def monomuon(sample, selector):
    selector = muonBase(sample, selector)
    selector.findOperator('LeptonSelection').setN(0, 1)

    if not sample.data:
        idsf = ROOT.IDSFWeight(ROOT.IDSFWeight.kMuon, 'MuonSF')
        idsf.addFactor(muonTightSF)
        idsf.setVariable(ROOT.IDSFWeight.kAbsEta, ROOT.IDSFWeight.kPt)
        selector.addOperator(idsf)

    """
    # single muon trigger efficiency ~ 90%
    selector.addOperator(ROOT.ConstantWeight(0.9))
    trackscale = ROOT.IDSFWeight(ROOT.IDSFWeight.kMuon, 'muonTrigSF')
    trackscale.addFactor(muonTrigSF)
    trackscale.setVariable(ROOT.IDSFWeight.kEta)
    selector.addOperator(trackscale)
    """

    return selector

def monomuonHadProxy(sample, selector):
    selector = muonBase(sample, selector)
    selector.findOperator('LeptonSelection').setN(0, 1)

    if not sample.data:
        idsf = ROOT.IDSFWeight(ROOT.IDSFWeight.kMuon, 'MuonSF')
        idsf.addFactor(muonTightSF)
        idsf.setVariable(ROOT.IDSFWeight.kAbsEta, ROOT.IDSFWeight.kPt)
        selector.addOperator(idsf)

    selector = hadProxy(sample, selector)

    return selector

def oppflavor(sample, selector):
    selector = muonBase(sample, selector)
    selector.findOperator('LeptonSelection').setN(1, 1)

    if not sample.data:
        idsf = ROOT.IDSFWeight(ROOT.IDSFWeight.kElectron, 'ElectronSF')
        idsf.addFactor(electronTightSF)
        idsf.setVariable(ROOT.IDSFWeight.kAbsEta, ROOT.IDSFWeight.kPt)
        selector.addOperator(idsf)

        ### might not be 100% correct because there is no check 
        ### that both electron and muon are tight >.>

        idsf = ROOT.IDSFWeight(ROOT.IDSFWeight.kMuon, 'MuonSF')
        idsf.addFactor(muonTightSF)
        idsf.setVariable(ROOT.IDSFWeight.kAbsEta, ROOT.IDSFWeight.kPt)
        selector.addOperator(idsf)

    return selector

def zee(sample, name):
    selector = ROOT.ZeeEventSelector(name)

    eeSel = selector.findOperator('EEPairSelection')
    eeSel.setMinPt(140.)

    sels = list(photonFullSelection)
    sels.remove('EVeto')

    for sel in sels:
        eeSel.addSelection(True, getattr(ROOT.PhotonSelection, sel))

    eeSel.addSelection(False, ROOT.PhotonSelection.EVeto)

    selector.findOperator('TauVeto').setIgnoreDecision(True)
    selector.findOperator('JetCleaning').setCleanAgainst(ROOT.JetCleaning.kTaus, False)

    return selector

def wenuall(sample, name):
    """
    Candidate-like selection but for W->enu, no pixel veto on the photon.
    """

    selector = monophotonBase(sample, ROOT.WenuSelector(name))

    # selector.addOperator(ROOT.IDSFWeight(ROOT.IDSFWeight.kPhoton, photonSF, 'photonSF'))
    # selector.addOperator(ROOT.ConstantWeight(1.01, 'extraSF'))
    if 'amcatnlo' in sample.fullname or 'madgraph' in sample.fullname: # ouh la la..
        selector.addOperator(ROOT.NNPDFVariation())

    photonSel = selector.findOperator('PhotonSelection')

    for sel in photonFullSelection:
        if sel != 'EVeto':
            photonSel.addSelection(True, getattr(ROOT.PhotonSelection, sel))

    photonSel.setMinPt(15.)

    return selector

def kfactor(generator):
    """
    Wrapper for applying the k-factor corrections to the selector returned by the generator in the argument.
    """

    def scaled(sample, name):
        selector = generator(sample, name)

        sname = sample.name.replace('gj04', 'gj').replace('znng-d', 'znng-130').replace('wnlg-d', 'wnlg-130').replace('0-d', '0').replace('zllg', 'znng')

        qcdSource = ROOT.TFile.Open(basedir + '/data/kfactor.root')
        corr = qcdSource.Get(sname)

        qcd = ROOT.PhotonPtWeight(corr, 'QCDCorrection')
        qcd.setPhotonType(ROOT.PhotonPtWeight.kPostShower) # if possible
        # qcd.setPhotonType(ROOT.PhotonPtWeight.kReco) # because nero doesn't have gen info saved

        for variation in ['renUp', 'renDown', 'facUp', 'facDown', 'scaleUp', 'scaleDown']:
            vcorr = qcdSource.Get(sname + '_' + variation)
            if vcorr:
                # print 'applying qcd var', variation, sample.name
                qcd.addVariation('qcd' + variation, vcorr)

        selector.addOperator(qcd)

        ewkSource = ROOT.TFile.Open(basedir + '/data/ewk_corr.root')
        corr = ewkSource.Get(sname)
        if corr:
            # print 'applying ewk', sample.name
            ewk = ROOT.PhotonPtWeight(corr, 'EWKNLOCorrection')
            ewk.setPhotonType(ROOT.PhotonPtWeight.kParton)

            for variation in ['Up', 'Down']:
                vcorr = ewkSource.Get(sname + '_' + variation)
                if vcorr:
                    # print 'applying ewk var', variation, sample.name
                    ewk.addVariation('ewk' + variation, vcorr)

            selector.addOperator(ewk)

        return selector

    return scaled

def wlnu(generator):
    """
    Wrapper for W->lnu sample to pick out non-electron decays only.
    """

    def filtered(sample, name):
        return generator(sample, ROOT.WlnuSelector(name))

    return filtered

def TagAndProbeBase(sample, selector):
    """
    Base for Z->ll tag and probe stuff.
    """

    if type(selector) is str: # this is a name for the selector
        selector = ROOT.EventSelector(selector)

    operators = [
        'MetFilters',
        'MuonVeto',
        'ElectronVeto',
        'TauVeto',
        'TagAndProbePairZ',
        'JetCleaning',
        'CopyMet',
        'JetMetDPhi',
        'HighMet'
        ]
    
    for op in operators:
        selector.addOperator(getattr(ROOT, op)())

    if not sample.data:
        selector.addOperator(ROOT.ConstantWeight(sample.crosssection / sample.sumw))
        selector.addOperator(ROOT.PUWeight(puWeight))

    selector.findOperator('MuonVeto').setIgnoreDecision(True)
    selector.findOperator('ElectronVeto').setIgnoreDecision(True)
    selector.findOperator('TauVeto').setIgnoreDecision(True)
    selector.findOperator('JetCleaning').setCleanAgainst(ROOT.JetCleaning.kTaus, False)
    # selector.findOperator('JetCleaning').setCleanAgainst(ROOT.JetCleaning.kElectrons, False)
    # selector.findOperator('JetCleaning').setCleanAgainst(ROOT.JetCleaning.kMuons, False)
    selector.findOperator('JetMetDPhi').setIgnoreDecision(True)
    selector.findOperator('HighMet').setThreshold(50.)
    selector.findOperator('HighMet').setIgnoreDecision(True)

    return selector

def zeeBase(sample, selector):
    """
    Select Z->ee events.
    """
    selector = TagAndProbeBase(sample, selector)
    if sample.data:
        selector.addOperator(ROOT.HLTFilter('HLT_Ele27_WPTight_Gsf'), 0)

    tnp = selector.findOperator('TagAndProbePairZ')
    tnp.setTagSpecies(ROOT.TagAndProbePairZ.kElectron)
    tnp.setProbeSpecies(ROOT.TagAndProbePairZ.kElectron)

    return selector

def zeeJets(sample, selector):
    """
    Require Z->ee plus at least one high pt jet.
    """
    selector = zeeBase(sample, selector)

    b2b = ROOT.ZJetBackToBack()
    b2b.setTagAndProbePairZ(selector.findOperator('TagAndProbePairZ'))
    b2b.setMinJetPt(100.)
    b2b.setMinDeltaPhi(3.)
    selector.addOperator(b2b)

    return selector

def zmmBase(sample, selector):
    """
    Select Z->mumu events.
    """
    selector = TagAndProbeBase(sample, selector)
    if sample.data:
        selector.addOperator(ROOT.HLTFilter('HLT_IsoMu20_OR_HLT_IsoTkMu20'), 0)

    tnp = selector.findOperator('TagAndProbePairZ')
    tnp.setTagSpecies(ROOT.TagAndProbePairZ.kMuon)
    tnp.setProbeSpecies(ROOT.TagAndProbePairZ.kMuon)
    
    return selector

def zmmJets(sample, selector):
    """
    Require Z->mumu plus at least one high pt jet.
    """
    selector = TagAndProbeBase(sample, selector)

    b2b = ROOT.ZJetBackToBack()
    b2b.setTagAndProbePairZ(selector.findOperator('TagAndProbePairZ'))
    b2b.setMinJetPt(100.)
    b2b.setMinDeltaPhi(3.)
    selector.addOperator(b2b)

    return selector

if needHelp:
    sys.argv.append('--help')
