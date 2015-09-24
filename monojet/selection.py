def build_selection(selection,bin0):

    selections = ['signal','Zll','Wln','monophoton','Zee','Wen']

    snippets = {
        #** monojet
        'leading jet pT':['jetP4[0].Pt()>110.',selections],
        #'leading jet eta':['abs(jetP4[0].Eta())<2.4',selections],
        'jet cleaning':['jetMonojetId[0]==1',selections],
        #'trailing jet':['(jetP4[1].Pt() < 30 || deltaPhi(jetP4[0].Phi(),jetP4[1].Phi())<2)',selections],
        'jet multiplicity':['@jetP4.size()<3',selections],
        'deltaPhi':['deltaPhi(jetP4[0].Phi(),metP4[0].Phi())>0.4',selections],
        #'trigger':['(triggerFired[0]==1 || triggerFired[1]==1)',selections],
        'lepton veto':['n_tightlep==0',['signal']],
        'pho veto':['@photonP4.size()==0',['signal','Zll','Wln']], 
        'tau veto':['@tauP4.size()==0',selections], 

        #** Control Regions
        'leading lep ID': ['n_tightlep==1',['Wln','Zll']],
        #'leading muon Iso': ['lep1IsIsolated',['Wln']],
        'Zmm':['n_looselep == 2 && n_tightlep > 0 && ((((lepPdgId)[0]*(lepPdgId)[1])== -169 && abs(vectorSumMass(lepP4[0].Px(),lepP4[0].Py(),lepP4[0].Pz(),lepP4[1].Px(),lepP4[1].Py(),lepP4[1].Pz())-91)<30))',['Zll']],
        'Zee':['n_looselep == 2 && n_tightlep > 0 && ((((lepPdgId)[0]*(lepPdgId)[1])== -121 && abs(vectorSumMass(lepP4[0].Px(),lepP4[0].Py(),lepP4[0].Pz(),lepP4[1].Px(),lepP4[1].Py(),lepP4[1].Pz())-91)<30))',['Zee']],
        #'dilepPt':['vectorSumPt(lepP4[0].Pt(),lepP4[0].Phi(),lepP4[1].Pt(),lepP4[2].Phi())>100',['Zll']],
        'Wln':['@lepP4.size()==1 && abs((lepPdgId)[0])==13 && mt > 50.',['Wln']],
        'Wen':['@lepP4.size()==1 && abs((lepPdgId)[0])==11 && mt > 50.',['Wen']],
        'monophoton':['photonP4[0].Pt() > 175 && abs(photonP4[0].Eta()) < 2.5 && n_looselep == 0 && @photonP4.size() == 1 && photonTightId[0] == 1',['monophoton']]
        }

    selectionString = ''
    for cut in snippets:
        if selection in snippets[cut][1]: 
            selectionString += snippets[cut][0]+'&&'

    met  = 'metP4[0].Pt()'

    analysis_bin = {}
    analysis_bin[0] = bin0

    #if selection.find('Zll')>-1: selectionString+='deltaPhi(jet1.Phi(),'+metZ+'Phi)>2 && '+metZ+'>'+str(analysis_bin[0])
    #elif selection.find('Wln')>-1: selectionString+='deltaPhi(jet1.Phi(),'+metW+'Phi)>2 && '+metW+'>'+str(analysis_bin[0])
    #else: 

    selectionString+=met+'>'+str(analysis_bin[0])

    return selectionString

