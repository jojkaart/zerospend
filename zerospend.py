#!/usr/bin/python
from decimal import Decimal
import traceback
import sys

from python-jsonrpc import ServiceProxy, JSONRPCException
bitcoind = ServiceProxy("http://user:password@localhost:8332/")

class Transaction:
  def __init__(self,txid):
    if len(txid) == 64:
      self.tx = bitcoind.getrawtransaction(txid,1)
    else:
      self.tx = bitcoind.decoderawtransaction(txid)
      self.tx['hex'] = txid
    self.vout = self.tx['vout']
    self.vin = self.tx['vin']
    self.fee = None
    self._totalValue = None
    
  def getSize(self):
    return len(self.tx['hex']) / 2

  def getFee(self):
    if self.fee == None:
      inputSum = sum((Transaction(vin['txid']).getVoutValue(vin['vout']) for vin in self.tx['vin']))
      outputSum = sum((vout['value'] for vout in self.tx['vout']))
      self.fee = inputSum - outputSum
    return self.fee

  def getFeeKB(self):
    return 1000 * self.getFee() / self.getSize()

  def getVoutValue(self,n):
    assert(self.vout[n]['n'] == n)
    return self.vout[n]['value'];

  def getTotalValue(self):
    if self._totalValue == None:
      self._totalValue = sum((vout['value'] for vout in self.tx['vout']))
    return self._totalValue
  
try:
  if len(sys.argv) < 3:
    print "Usage: %s <fee> <target address> [<input address> <input address>]" % (sys.argv[0],)
    print "input addresses are optional. If present, they will be used to filter"
    print "what 0conf transactions are used as input"
    exit(0)
  targetFee = Decimal(sys.argv[1])
  targetaddress = sys.argv[2]
  inputs = sys.argv[3:]

  zeroconfs = bitcoind.listunspent(0,0,inputs);

  print "Found the following inputs:"
  for input in zeroconfs:
    print "%s: %0.8f BTC with %d confirmations in %s" % (input['account'], input['amount'], input['confirmations'], input['address'])

  inputs = [Transaction(input['txid']) for input in zeroconfs]
  vinlist = [dict(txid=input['txid'],vout=input['vout']) for input in zeroconfs]
  inputSum = sum((input['amount'] for input in zeroconfs))
  inputFee = sum((tx.getFee() for tx in inputs))
  inputSize = sum((tx.getSize() for tx in inputs))
  
  draftOutput = dict([(targetaddress,inputSum)]);
  draft = bitcoind.createrawtransaction(vinlist,draftOutput)
  draftSize = len(draft)/2
  signedDraft = bitcoind.signrawtransaction(draft)
  signedSize = len(signedDraft['hex'])/2
  

  totalSize = inputSize + signedSize
  totalFee = targetFee * (totalSize / Decimal('1000.0')) - inputFee

  # make sure the fee makes some sense on it's own
  totalFee = max(totalFee,targetFee * signedSize / 1000,Decimal('0.00005'))
  
  outputAmount = inputSum - totalFee

  output = dict([(targetaddress,outputAmount)]);
  unsigned = bitcoind.createrawtransaction(vinlist,output)
  signed = bitcoind.signrawtransaction(unsigned)
  final = Transaction(signed['hex'])

  print "Would create the following transaction:"
  print "Size %d bytes. Fee %0.8f BTC." % (final.getSize(),final.getFee())
  for vout in final.vout:
    print "Output #%d: %0.8f BTC to %s" % (vout['n'],vout['value'],vout['scriptPubKey']['addresses'][0])
#  print "Fee / kb %0.8f BTC/kb" % (totalFee * 1000 / signedSize,)
  print "Fee / kb counting inputs %0.8f BTC/kb" % ((totalFee+inputFee) * 1000 / (inputSize + signedSize),)
#  print draftSize,signedSize,inputSize,inputFee
#  print inputSum, totalFee, outputAmount


except JSONRPCException, e:
  print e.error
  