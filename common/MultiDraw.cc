#include "MultiDraw.h"

#include "TFile.h"
#include "TBranch.h"
#include "TGraph.h"
#include "TF1.h"
#include "TError.h"
#include "TLeafF.h"
#include "TLeafD.h"

#include <stdexcept>
#include <cstring>
#include <iostream>

/*
  TFormula has no foolproof mechanism to signal a failure of expression compilation.
  For normal expressions like TTreeFormula f("formula", "bogus", tree), we get f.GetTree() == 0.
  However if a TTreePlayer function (Sum$, Max$, etc.) is used, the top-level expression
  is considered valid even if the enclosed expression is not, and GetTree() returns the tree
  address.
  The only way we catch all compilation failures is to use the error message using ROOT
  error handling mechanism.
*/
Int_t gLastErrorLevel = 0;
void MyErrorHandler(Int_t level, Bool_t abort_bool, const char *location, const char *msg)
{
  gLastErrorLevel = level;
  DefaultErrorHandler(level, abort_bool, location, msg);
}

//! A wrapper for TTreeFormulaCached creation
TTreeFormula*
NewTTreeFormula(char const* _name, char const* _expr, TTree* _tree)
{
  gLastErrorLevel = 0;
  auto* errh(SetErrorHandler(MyErrorHandler));

  auto* formula(new TTreeFormula(_name, _expr, _tree));

  SetErrorHandler(errh);

  if (formula->GetTree() == nullptr || gLastErrorLevel == kError) {
    // compilation failed
    delete formula;
    return nullptr;
  }

  return formula;
}

//! A wrapper for TTreeFormulaCached creation
TTreeFormulaCached*
NewTTreeFormulaCached(char const* _name, char const* _expr, TTree* _tree)
{
  gLastErrorLevel = 0;
  auto* errh(SetErrorHandler(MyErrorHandler));

  auto* formula(new TTreeFormulaCached(_name, _expr, _tree));

  SetErrorHandler(errh);

  if (formula->GetTree() == nullptr || gLastErrorLevel == kError) {
    // compilation failed
    delete formula;
    return nullptr;
  }

  return formula;
}

Int_t
TTreeFormulaCached::GetNdata()
{
  if (fNdataCache < 0) {
    fNdataCache = TTreeFormula::GetNdata();
    fCache.assign(fNdataCache, std::pair<Bool_t, Double_t>(false, 0.));
  }

  return fNdataCache;
}

Double_t
TTreeFormulaCached::EvalInstance(Int_t _i, char const* _stringStack[]/* = nullptr*/)
{
  if (_i >= int(fCache.size()))
    return 0.;

  if (!fCache[_i].first) {
    fCache[_i].first = true;
    fCache[_i].second = TTreeFormula::EvalInstance(_i, _stringStack);
  }

  return fCache[_i].second;
}


ExprFiller::ExprFiller(TTreeFormula* _cuts/* = nullptr*/, TTreeFormula* _reweight/* = nullptr*/) :
  cuts_(_cuts),
  reweight_(_reweight)
{
}

ExprFiller::ExprFiller(ExprFiller const& _orig) :
  ownFormulas_(_orig.ownFormulas_)
{
  if (ownFormulas_) {
    for (unsigned iD(0); iD != _orig.getNdim(); ++iD) {
      auto& oexpr(*_orig.getExpr(iD));
      auto* formula(NewTTreeFormula(oexpr.GetName(), oexpr.GetTitle(), oexpr.GetTree()));
      if (formula == nullptr)
        throw std::runtime_error("Failed to compile formula.");

      exprs_.push_back(formula);
    }

    if (_orig.cuts_ != nullptr) {
      cuts_ = NewTTreeFormula(_orig.cuts_->GetName(), _orig.cuts_->GetTitle(), _orig.cuts_->GetTree());
      if (cuts_ == nullptr)
        throw std::runtime_error("Failed to compile cuts.");
    }

    if (_orig.reweight_ != nullptr) {
      reweight_ = NewTTreeFormula(_orig.reweight_->GetName(), _orig.reweight_->GetTitle(), _orig.reweight_->GetTree());
      if (reweight_ == nullptr)
        throw std::runtime_error("Failed to compile reweight.");
    }
  }
  else {
    exprs_ = _orig.exprs_;
    cuts_ = _orig.cuts_;
    reweight_ = _orig.reweight_;
  }
}

ExprFiller::~ExprFiller()
{
  if (ownFormulas_) {
    delete cuts_;
    delete reweight_;

    for (auto* expr : exprs_)
      delete expr;
  }
}

void
ExprFiller::updateTree()
{
  for (auto* expr : exprs_)
    expr->UpdateFormulaLeaves();

  if (cuts_ != nullptr)
    cuts_->UpdateFormulaLeaves();

  if (reweight_ != nullptr)
    reweight_->UpdateFormulaLeaves();
}

void
ExprFiller::fill(std::vector<double> const& _eventWeights, std::vector<bool> const* _presel/* = nullptr*/)
{
  // using the first expr for the number of instances
  unsigned nD(exprs_.at(0)->GetNdata());
  // need to call GetNdata before EvalInstance
  if (cuts_ != nullptr)
    cuts_->GetNdata();

  if (printLevel_ > 3)
    std::cout << "          " << getObj()->GetName() << "::fill() => " << nD << " iterations" << std::endl;

  if (_presel != nullptr && _presel->size() < nD)
    nD = _presel->size();

  bool cutsLoaded(false);
  bool loaded(false);

  for (unsigned iD(0); iD != nD; ++iD) {
    if (_presel != nullptr && !(*_presel)[iD])
      continue;

    if (cuts_ != nullptr) {
      if (!cutsLoaded && iD != 0)
        cuts_->EvalInstance(0);

      cutsLoaded = true;

      if (cuts_->EvalInstance(iD) == 0.)
        continue;
    }

    ++counter_;

    if (!loaded) {
      for (unsigned iE(0); iE != exprs_.size(); ++iE) {
        exprs_[iE]->GetNdata();
        if (iD != 0) // need to always call EvalInstance(0)
          exprs_[iE]->EvalInstance(0);
      }
      if (reweight_ != nullptr) {
        reweight_->GetNdata();
        if (iD != 0)
          reweight_->EvalInstance(0);
      }
    }

    loaded = true;

    if (iD < _eventWeights.size())
      entryWeight_ = _eventWeights[iD];
    else
      entryWeight_ = _eventWeights.back();

    if (reweight_ != nullptr)
      entryWeight_ *= reweight_->EvalInstance(iD);

    doFill_(iD);
  }
}


Plot::Plot(TH1& _hist, TTreeFormula& _expr, TTreeFormula* _cuts/* = nullptr*/, TTreeFormula* _reweight/* = nullptr*/, OverflowMode _mode/* = kNoOverflowBin*/) :
  ExprFiller(_cuts, _reweight),
  hist_(&_hist),
  overflowMode_(_mode)
{
  exprs_.push_back(&_expr);
}

Plot::Plot(Plot const& _orig) :
  ExprFiller(_orig),
  hist_(_orig.hist_),
  overflowMode_(_orig.overflowMode_)
{
}

void
Plot::doFill_(unsigned _iD)
{
  if (printLevel_ > 3)
    std::cout << "            Fill(" << exprs_[0]->EvalInstance(_iD) << "; " << entryWeight_ << ")" << std::endl;

  double x(exprs_[0]->EvalInstance(_iD));

  switch (overflowMode_) {
  case Plot::kNoOverflowBin:
    break;
  case Plot::kDedicated:
    if (x > hist_->GetXaxis()->GetBinLowEdge(hist_->GetNbinsX()))
      x = hist_->GetXaxis()->GetBinLowEdge(hist_->GetNbinsX());
    break;
  case Plot::kMergeLast:
    if (x > hist_->GetXaxis()->GetBinUpEdge(hist_->GetNbinsX()))
      x = hist_->GetXaxis()->GetBinLowEdge(hist_->GetNbinsX());
    break;
  }

  hist_->Fill(x, entryWeight_);
}


Tree::Tree(TTree& _tree, TTreeFormula* _cuts/* = nullptr*/, TTreeFormula* _reweight/* = nullptr*/) :
  ExprFiller(_cuts, _reweight),
  tree_(&_tree)
{
  tree_->Branch("weight", &entryWeight_, "weight/D");

  bvalues_.reserve(NBRANCHMAX);
}

Tree::Tree(Tree const& _orig) :
  ExprFiller(_orig),
  tree_(_orig.tree_),
  bvalues_(_orig.bvalues_)
{
  tree_->SetBranchAddress("weight", &entryWeight_);

  bvalues_.reserve(NBRANCHMAX);

  // rely on the fact that the branch order should be aligned
  auto* branches(tree_->GetListOfBranches());
  for (int iB(0); iB != branches->GetEntries(); ++iB)
    tree_->SetBranchAddress(branches->At(iB)->GetName(), &bvalues_[iB]);
}

void
Tree::addBranch(char const* _bname, TTreeFormula& _expr)
{
  if (bvalues_.size() == NBRANCHMAX)
    throw std::runtime_error("Cannot add any more branches");

  bvalues_.resize(bvalues_.size() + 1);
  tree_->Branch(_bname, &bvalues_.back(), TString::Format("%s/D", _bname));

  exprs_.push_back(&_expr);
}

void
Tree::doFill_(unsigned _iD)
{
  if (printLevel_ > 3)
    std::cout << "            Fill(";

  for (unsigned iE(0); iE != exprs_.size(); ++iE) {
    if (printLevel_ > 3) {
      std::cout << exprs_[iE]->EvalInstance(_iD);
      if (iE != exprs_.size() - 1)
        std::cout << ", ";
    }

    bvalues_[iE] = exprs_[iE]->EvalInstance(_iD);
  }

  if (printLevel_ > 3)
    std::cout << "; " << entryWeight_ << ")" << std::endl;

  tree_->Fill();
}


MultiDraw::MultiDraw(char const* _treeName/* = "events"*/) :
  tree_(_treeName)
{
}

MultiDraw::~MultiDraw()
{
  for (auto* plots : {&postFull_, &postBase_, &unconditional_}) {
    for (auto* plot : *plots)
      delete plot;
  }

  for (auto& ff : library_)
    delete ff.second;
}

void
MultiDraw::setBaseSelection(char const* _cuts)
{
  if (baseSelection_ != nullptr) {
    deleteFormula_(baseSelection_);
    baseSelection_ = nullptr;
  }

  if (!_cuts || std::strlen(_cuts) == 0)
    return;

  baseSelection_ = getFormula_(_cuts);
  if (baseSelection_ == nullptr)
    std::cerr << "Failed to compile base selection " << _cuts << std::endl;
}

void
MultiDraw::setFullSelection(char const* _cuts)
{
  if (fullSelection_ != nullptr) {
    deleteFormula_(fullSelection_);
    fullSelection_ = nullptr;
  }

  if (!_cuts || std::strlen(_cuts) == 0)
    return;

  fullSelection_ = getFormula_(_cuts);
  if (fullSelection_ == nullptr)
    std::cerr << "Failed to compile full selection " << _cuts << std::endl;
}

void
MultiDraw::setReweight(char const* _expr, TObject const* _source/* = nullptr*/)
{
  if (reweightExpr_ != nullptr) {
    deleteFormula_(reweightExpr_);
    reweightExpr_ = nullptr;
  }

  reweight_ = nullptr;

  if (!_expr || std::strlen(_expr) == 0)
    return;

  reweightExpr_ = getFormula_(_expr);
  if (reweightExpr_ == nullptr) {
    std::cerr << "Failed to compile reweight expression " << _expr << std::endl;
    return;
  }

  if (_source != nullptr) {
    if (_source->InheritsFrom(TH1::Class())) {
      auto* source(static_cast<TH1 const*>(_source));

      reweight_ = [this, source](std::vector<double>& _values) {
        _values.clear();

        unsigned nD(this->reweightExpr_->GetNdata());

        for (unsigned iD(0); iD != nD; ++iD) {
          double x(this->reweightExpr_->EvalInstance(iD));

          int iX(source->FindFixBin(x));
          if (iX == 0)
            iX = 1;
          else if (iX > source->GetNbinsX())
            iX = source->GetNbinsX();

          _values.push_back(source->GetBinContent(iX));
        }
      };
    }
    else if (_source->InheritsFrom(TGraph::Class())) {
      auto* source(static_cast<TGraph const*>(_source));

      int n(source->GetN());
      double* xvals(source->GetX());
      for (int i(0); i != n - 1; ++i) {
        if (xvals[i] >= xvals[i + 1])
          throw std::runtime_error("Reweight TGraph source must have xvalues in increasing order");
      }

      reweight_ = [this, source](std::vector<double>& _values) {
        _values.clear();

        unsigned nD(this->reweightExpr_->GetNdata());

        for (unsigned iD(0); iD != nD; ++iD) {
          double x(this->reweightExpr_->EvalInstance(iD));

          int n(source->GetN());
          double* xvals(source->GetX());

          double* b(std::upper_bound(xvals, xvals + n, x));
          if (b == xvals + n)
            _values.push_back(source->GetY()[n - 1]);
          else if (b == xvals)
            _values.push_back(source->GetY()[0]);
          else {
            // interpolate
            int low(b - xvals - 1);
            double dlow(x - xvals[low]);
            double dhigh(xvals[low + 1] - x);

            _values.push_back((source->GetY()[low] * dhigh + source->GetY()[low + 1] * dlow) / (xvals[low + 1] - xvals[low]));
          }
        }
      };
    }
    else if (_source->InheritsFrom(TF1::Class())) {
      auto* source(static_cast<TF1 const*>(_source));

      reweight_ = [this, source](std::vector<double>& _values) {
        _values.clear();

        unsigned nD(this->reweightExpr_->GetNdata());

        for (unsigned iD(0); iD != nD; ++iD) {
          double x(this->reweightExpr_->EvalInstance(iD));

          _values.push_back(source->Eval(x));
        }
      };
    }
    else
      throw std::runtime_error("Incompatible object passed as reweight source");
  }
  else {
    reweight_ = [this](std::vector<double>& _values) {
      _values.clear();

      unsigned nD(this->reweightExpr_->GetNdata());

      for (unsigned iD(0); iD != nD; ++iD)
        _values.push_back(this->reweightExpr_->EvalInstance(iD));
    };
  }
}

void
MultiDraw::addPlot(TH1* _hist, char const* _expr, char const* _cuts/* = ""*/, bool _applyBaseline/* = true*/, bool _applyFullSelection/* = false*/, char const* _reweight/* = ""*/, Plot::OverflowMode _overflowMode/* = Plot::kNoOverflow*/)
{
  TTreeFormulaCached* exprFormula(getFormula_(_expr));
  if (exprFormula == nullptr) {
    std::cerr << "Plot " << _hist->GetName() << " cannot be added (invalid expression)" << std::endl;
    return;
  }

  auto newPlot([_hist, _overflowMode, exprFormula](TTreeFormula* _cutsFormula, TTreeFormula* _reweightFormula)->ExprFiller* {
      return new Plot(*_hist, *exprFormula, _cutsFormula, _reweightFormula, _overflowMode);
    });

  if (printLevel_ > 1) {
    std::cout << "\nAdding Plot " << _hist->GetName() << " with expression " << _expr << std::endl;
    if (_cuts != nullptr && std::strlen(_cuts) != 0)
      std::cout << " Cuts: " << _cuts << std::endl;
    if (_reweight != nullptr && std::strlen(_reweight) != 0)
      std::cout << " Reweight: " << _reweight << std::endl;
  }

  addObj_(_cuts, _applyBaseline, _applyFullSelection, _reweight, newPlot);
}

void
MultiDraw::addTree(TTree* _tree, char const* _cuts/* = ""*/, bool _applyBaseline/* = true*/, bool _applyFullSelection/* = false*/, char const* _reweight/* = ""*/)
{
  auto newTree([_tree](TTreeFormula* _cutsFormula, TTreeFormula* _reweightFormula)->ExprFiller* {
      return new Tree(*_tree, _cutsFormula, _reweightFormula);
    });

  if (printLevel_ > 1) {
    std::cout << "\nAdding Tree " << _tree->GetName() << std::endl;
    if (_cuts != nullptr && std::strlen(_cuts) != 0)
      std::cout << " Cuts: " << _cuts << std::endl;
    if (_reweight != nullptr && std::strlen(_reweight) != 0)
      std::cout << " Reweight: " << _reweight << std::endl;
  }

  addObj_(_cuts, _applyBaseline, _applyFullSelection, _reweight, newTree);
}

void
MultiDraw::addTreeBranch(TTree* _tree, char const* _bname, char const* _expr)
{
  auto* exprFormula(getFormula_(_expr));
  if (exprFormula == nullptr) {
    std::cerr << "Branch " << _bname << " cannot be added (invalid expression)" << std::endl;
    return;
  }

  for (auto* plots : {&postFull_, &postBase_, &unconditional_}) {
    for (auto* plot : *plots) {
      if (plot->getObj() == _tree) {
        if (printLevel_ > 1)
          std::cout << "Adding a branch " << _bname << " to tree " << plot->getObj()->GetName() << " with expression " << _expr << std::endl;

        static_cast<Tree*>(plot)->addBranch(_bname, *exprFormula);
      }
    }
  }
}

void
MultiDraw::addObj_(char const* _cuts, bool _applyBaseline, bool _applyFullSelection, char const* _reweight, ObjGen const& _gen)
{
  TTreeFormulaCached* cutsFormula(nullptr);
  if (_cuts != nullptr && std::strlen(_cuts) != 0) {
    cutsFormula = getFormula_(_cuts);
    if (cutsFormula == nullptr) {
      std::cerr << "Failed to compile cuts " << _cuts << std::endl;
      return;
    }
  }

  TTreeFormulaCached* reweightFormula(nullptr);
  if (_reweight != nullptr && std::strlen(_reweight) != 0) {
    reweightFormula = getFormula_(_reweight);
    if (reweightFormula == nullptr) {
      std::cerr << "Failed to compile reweight " << _reweight << std::endl;
      return;
    }
  }

  std::vector<ExprFiller*>* stack(nullptr);
  if (_applyBaseline) {
    if (_applyFullSelection)
      stack = &postFull_;
    else
      stack = &postBase_;
  }
  else
    stack = &unconditional_;

  stack->push_back(_gen(cutsFormula, reweightFormula));
}

TTreeFormulaCached*
MultiDraw::getFormula_(char const* _expr)
{
  auto fItr(library_.find(_expr));
  if (fItr != library_.end()) {
    fItr->second->SetNRef(fItr->second->GetNRef() + 1);
    return fItr->second;
  }

  auto* f(NewTTreeFormulaCached("formula", _expr, &tree_));
  if (f == nullptr)
    return nullptr;

  library_.emplace(_expr, f);

  return f;
}

void
MultiDraw::deleteFormula_(TTreeFormulaCached* _formula)
{
  if (_formula->GetNRef() == 1) {
    library_.erase(_formula->GetTitle());
    delete _formula;
  }
}

void
MultiDraw::fillPlots(long _nEntries/* = -1*/, long _firstEntry/* = 0*/)
{
  float* weightF(nullptr);
  double weight(1.);
  unsigned eventNumber;
  TBranch* weightBranch(nullptr);
  TBranch* eventNumberBranch(nullptr);

  for (auto* plots : {&postFull_, &postBase_, &unconditional_}) {
    for (auto* plot : *plots) {
      plot->setPrintLevel(printLevel_);
      plot->resetCount();
    }
  }

  std::vector<double> eventWeights;
  std::vector<bool>* baseResults(nullptr);
  std::vector<bool>* fullResults(nullptr);

  if (baseSelection_ && baseSelection_->GetMultiplicity() != 0) {
    if (printLevel_ > 1)
      std::cout << "\n\nBase selection is based on an array." << std::endl;

    baseResults = new std::vector<bool>;
  }
  if (fullSelection_ && fullSelection_->GetMultiplicity() != 0) {
    if (printLevel_ > 1)
      std::cout << "\nFull selection is based on an array." << std::endl;

    fullResults = new std::vector<bool>;
  }

  long printEvery(10000);
  if (printLevel_ == 2)
    printEvery = 10000;
  else if (printLevel_ == 3)
    printEvery = 100;
  else if (printLevel_ >= 4)
    printEvery = 1;

  long iEntry(_firstEntry);
  long iEntryMax(_firstEntry + _nEntries);
  long iLocalEntry(0);
  int treeNumber(-1);
  unsigned passBase(0);
  unsigned passFull(0);
  while (iEntry != iEntryMax && (iLocalEntry = tree_.LoadTree(iEntry++)) >= 0) {
    if (printLevel_ >= 0 && iEntry % printEvery == 1) {
      std::cout << "\r      " << iEntry << " events";
      if (printLevel_ > 2)
        std::cout << std::endl;
    }

    if (treeNumber != tree_.GetTreeNumber()) {
      if (printLevel_ > 1)
        std::cout << "      Opened a new file: " << tree_.GetCurrentFile()->GetName() << std::endl;

      treeNumber = tree_.GetTreeNumber();

      if (weightBranchName_.Length() != 0) {
        weightBranch = tree_.GetBranch(weightBranchName_);
        if (!weightBranch)
          throw std::runtime_error(("Could not find branch " + weightBranchName_).Data());

        auto* leaves(weightBranch->GetListOfLeaves());
        if (leaves->GetEntries() == 0) // ??
          throw std::runtime_error(("Branch " + weightBranchName_ + " does not have any leaves").Data());

        auto* leaf(static_cast<TLeaf*>(leaves->At(0)));

        if (leaf->InheritsFrom(TLeafF::Class())) {
          if (weightF == nullptr)
            weightF = new float;
          weightBranch->SetAddress(weightF);
        }
        else if (leaf->InheritsFrom(TLeafD::Class())) {
          if (weightF != nullptr) {
            // we don't really need to handle a case like this (trees with different weight branch types are mixed), but we can..
            delete weightF;
            weightF = nullptr;
          }
          weightBranch->SetAddress(&weight);
        }
        else
          throw std::runtime_error(("I do not know how to read the leaf type of branch " + weightBranchName_).Data());
      }

      if (prescale_ > 1) {
        eventNumberBranch = tree_.GetBranch("eventNumber");
        if (!eventNumberBranch)
          throw std::runtime_error("Event number not available");

        eventNumberBranch->SetAddress(&eventNumber);
      }

      for (auto& ff : library_)
        ff.second->UpdateFormulaLeaves();
    }

    if (prescale_ > 1) {
      eventNumberBranch->GetEntry(iLocalEntry);

      if (eventNumber % prescale_ != 0)
        continue;
    }

    // Reset formula cache
    for (auto& ff : library_)
      ff.second->ResetCache();

    if (weightBranch) {
      weightBranch->GetEntry(iLocalEntry);
      if (weightF != nullptr)
        weight = *weightF;

      if (printLevel_ > 3)
        std::cout << "        Input weight " << weight << std::endl;
    }

    if (reweight_) {
      reweight_(eventWeights);
      if (eventWeights.empty())
        continue;

      for (double& w : eventWeights)
        w *= weight * constWeight_;
    }
    else
      eventWeights.assign(1, weight * constWeight_);

    if (printLevel_ > 3) {
      std::cout << "         Global weights: ";
      for (double w : eventWeights)
        std::cout << w << " ";
      std::cout << std::endl;
    }    

    // Plots that do not require passing the baseline cut
    for (auto* plot : unconditional_) {
      if (printLevel_ > 3)
        std::cout << "        Filling " << plot->getObj()->GetName() << std::endl;

      plot->fill(eventWeights);
    }

    // Baseline cut
    if (baseSelection_) {
      unsigned nD(baseSelection_->GetNdata());

      if (printLevel_ > 2)
        std::cout << "        Base selection has " << nD << " iterations" << std::endl;

      bool any(false);

      if (baseResults)
        baseResults->assign(nD, false);

      for (unsigned iD(0); iD != nD; ++iD) {
        if (baseSelection_->EvalInstance(iD) != 0.) {
          any = true;

          if (printLevel_ > 2)
            std::cout << "        Base selection " << iD << " is true" << std::endl;

          if (baseResults)
            (*baseResults)[iD] = true;
          else
            break; // no need to evaluate more
        }
      }

      if (!any)
        continue;
    }

    ++passBase;

    // Plots that require passing the baseline cut but not the full cut
    for (auto* plot : postBase_) {
      if (printLevel_ > 3)
        std::cout << "        Filling " << plot->getObj()->GetName() << std::endl;

      plot->fill(eventWeights, baseResults);
    }

    // Full cut
    if (fullSelection_) {
      unsigned nD(fullSelection_->GetNdata());

      if (printLevel_ > 2)
        std::cout << "        Full selection has " << nD << " iterations" << std::endl;

      bool any(false);

      if (fullResults)
        fullResults->assign(nD, false);

      // fullResults for iD >= baseResults->size() will never be true
      if (baseResults && baseResults->size() < nD)
        nD = baseResults->size();

      bool loaded(false);

      for (unsigned iD(0); iD != nD; ++iD) {
        if (baseResults && !(*baseResults)[iD])
          continue;

        if (!loaded && iD != 0)
          fullSelection_->EvalInstance(0);

        loaded = true;

        if (fullSelection_->EvalInstance(iD) != 0.) {
          any = true;

          if (printLevel_ > 2)
            std::cout << "        Full selection " << iD << " is true" << std::endl;

          if (fullResults)
            (*fullResults)[iD] = true;
          else
            break;
        }
      }

      if (!any)
        continue;
    }

    ++passFull;

    // Plots that require all cuts
    for (auto* plot : postFull_) {
      if (printLevel_ > 3)
        std::cout << "        Filling " << plot->getObj()->GetName() << std::endl;

      plot->fill(eventWeights, fullResults);
    }
  }

  delete baseResults;
  delete fullResults;
  delete weightF;

  totalEvents_ = iEntry;

  if (printLevel_ >= 0) {
    std::cout << "\r      " << iEntry << " events";
    std::cout << std::endl;
  }

  if (printLevel_ > 0) {
    std::cout << "      " << passBase << " passed base selection" << std::endl;
    std::cout << "      " << passFull << " passed full selection" << std::endl;

    for (auto* plots : {&postFull_, &postBase_, &unconditional_}) {
      for (auto* plot : *plots)
        std::cout << "        " << plot->getObj()->GetName() << ": " << plot->getCount() << std::endl;
    }
  }
}
