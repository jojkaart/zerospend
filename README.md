# Zerospend

A word of warning though. This code is untested as of yet. There's been basic testing but it's not been used to create any transactions that were broadcast.
In fact, the current code won't broadcast anything. Making it do that is a one-liner though.

Zerospend is a tool for sending bitcoins from inputs that have 0 confirmation.
There's a concept called Parent Pays For Child that most miners use these days. This is a tool for taking advantage of this feature.

So, if the following apply, this tool is for you:
- you have incoming 0 confirmation transactions that are taking forever
- you are running bitcoind (or a compatible RPC server)
- you're receiving those transactions into your bitcoind wallet

If the last point does not hold for you, it should be relatively simple to modify this code to handle even that case.
However, in such a case, you'll either need access to the private keys or a way to have your wallet sign a transaction it didn't create itself.
