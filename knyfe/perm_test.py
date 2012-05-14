import numpy as np
import itertools
from scipy.misc import comb as bincoef
import random

#########################################################################
# GENERATORS
#########################################################################


def sign_permutations(length):
    """ Memory efficient generator: generate all n^2 sign permutations. """ 
    # return a generator which generates the product of "length" smaller 
    # generators of (-1 or +1) (i.e. the unrolled signs, evaulated as needed)
    return itertools.product([-1, 1], repeat=length)

def random_product(*args, **kwds):
    """ Random selection from itertools.product(*args, **kwds). """
    pools = map(tuple, args) * kwds.get('repeat', 1)
    limiter = 0
    generate_limit = kwds.get('generate_limit', None)
    while True if generate_limit == None else limiter < generate_limit:
      limiter = limiter + 1
      yield tuple(random.choice(pool) for pool in pools)

def random_sign_permutations(length, limit):
    """ Random sign permutation generator. """
    return random_product([-1, 1], repeat=length, generate_limit=limit)

def binary_combinations(length, sublength, comb_function=itertools.combinations, limit=None):
    """ Memory efficient generator: generate all length choose sublength combinations. """ 

    # get the combination indices, support both infinite and finite length generators
    combination_indices = comb_function(range(length), sublength, limit) if limit else comb_function(range(length), sublength)

    def indices_to_sign_vectors():
      """ Generates sign vectors from indices. """
      for index_tuple in combination_indices:
        for i in xrange(length):
          yield 1 if index_tuple.count(i) > 0 else 0

    def grouper(n, iterable, fillvalue=None):
      " For grouping a generated stream into tuples. "
      args = [iter(iterable)] * n
      return itertools.izip_longest(fillvalue=fillvalue, *args)

    # generate all combinations, grouped into tuples
    return grouper(length, indices_to_sign_vectors())

def random_combination(iterable, r, limit=None):
    """ Random selection from itertools.combinations(iterable, r). """
    pool = tuple(iterable)
    n = len(pool)
    limiter = 0
    comb = bincoef(len(iterable), r)
    print comb
    comb_indices = random.sample(xrange(comb), limit)

    while True if limit == None else limiter < limit:
      print comb_indices[limiter]
      perm = get_nth_perm(pool, comb_indices[limiter])
      subpool = sorted(perm[:r])
      indices = sorted(random.sample(xrange(n), r))
      print tuple(pool[i] for i in indices), subpool, perm
      limiter = limiter + 1
      yield tuple(pool[i] for i in indices)


def _progress_bar(self, max=100, label=""):
    class Progress:
        def __init__(self, max=100, label=""):
            self.value = 1
            self.label = label
            self.max = max

        def set(self, value):
            self.value = value
            p50 = int(50.0 * value / self.max)
            if value >= self.max:
                self.clear()
            else:
                sys.stdout.write("\r" + "|"*p50 + "\033[30m" + "·"*(50-p50) + "\033[0m %02d%% %s" % (p50*2, self.label))
                sys.stdout.flush()
        def advance(self):
            self.set(self.value + 1)

        def clear(self):
            sys.stdout.write("\r"+" "*(80 + len(self.label))+"\r")
            sys.stdout.flush()
    return Progress(max, label)


def permutation_test(self, other, variables=None, ranked=False, two_samples=False, limit=1000):
    """Performs a permutation test on the given or the default dependent variables.
    If two_samples is True, will conduct a two-sample test. Otherwise a one-sample test will be conducted.
    If ranked is True, a Wilcoxon / Wilcoxon-Mann-Whitney test will be used for the one-sample /
    two-sample case, respectively. Otherwise a Fisher / Pitman test will be conducted."""        
    variables = self._np1d(variables, fallback = self.dependent)

    for var in variables:
        A = self.get(var)
        B = other.get(var)

        if not two_samples:
            D = [a - b for a, b in zip(A, B)]
            if ranked:
                D = self._signed_rank(D)
            result = perm_test.one_sample(D, progress_bar = self._progress_bar(), limit=limit)
        else:
            if ranked:
                D = self._rank(np.concatenate((A, B)))                   
                A, B = D[:len(A)], D[len(A):]
            result = perm_test.two_sample(A, B, progress_bar = self._progress_bar(), limit=limit)
    return result



def _signed_rank(self, values):
    """Returns the signed rank of a list of values"""
    lambda_signs = np.vectorize(lambda num: 1 if num >= 0 else -1)
    signs = lambda_signs(values)
    ranks = np.round(stats.rankdata(np.abs(values))).astype(int)
    return signs*ranks

def signed_rank(self, attribute):
    """Returns the signed ranks of the data of the given attribute"""
    values = self.get(attribute)
    return self._signed_rank(values)

def _rank(self, values):
    """Returns the ranks of the data of a list of values"""
    ranks = np.round(stats.rankdata(values)).astype(int)
    return ranks

def rank(self, attribute):
    """Returns the ranks of the data of the given attribute"""
    values = self.get(attribute)        
    return self._rank(values)



# def random_combination(iterable, r, limit=1000):
#     """ Random selection from itertools.combinations(iterable, r). """    
#     pool = tuple(iterable)
#     # number of 
#     comb = bincoef(len(iterable), r)
#     comb_indices = random.sample(xrange(comb), limit)
#     n = len(pool)
#     limiter = 0
#     for i in comb_indices:
#       perm = get_nth_perm(pool, i)
#       subpool = sorted(perm[:r])
#       yield tuple(subpool)

def get_nth_perm(seq, index):
    "Returns the <index>th permutation of <seq>"
    seqc= list(seq[:])
    seqn= [seqc.pop()]
    divider= 2 # divider is meant to be len(seqn)+1, just a bit faster
    while seqc:
        index, new_index= index//divider, index%divider
        seqn.insert(new_index, seqc.pop())
        divider+= 1
    return seqn


#########################################################################
# ACTUAL TESTS
#########################################################################

def one_sample(A, limit = 10000, progress_bar = None):
    """ Conducts a permutation test on the input data"""
    stat_ref = np.sum(A)
    # count permutation test statistics <=, >=, or ||>=|| than reference stat   
    counts = np.array([0,0,0]) # (lesser, greater, more extreme)
    total_perms = 2**len(A)
    if total_perms < limit:
        limit = total_perms
    if progress_bar:
        progress_bar.max = limit
        progress_bar.label = "of %d permutations" % progress_bar.max
    for sign_row in sign_permutations(len(A)):
        stat_this = np.sum(np.array(A)*sign_row)
        counts = counts + stat_compare(stat_ref,stat_this)
        if progress_bar:
           progress_bar.advance()

    # return p-values for lower, upper, and two-tail tests (FP number)
    return counts / 2.0**len(A)

def two_sample(A, B, limit = 10000, progress_bar = None):
    """ Conducts a permutation test on the input data, transformed by fun. """
    # apply transformation to input data (e.g. signed-rank for WMW)
    data = np.concatenate((A, B))
    stat_ref = np.sum(A)
    # count permutation test statistics <=, >=, or ||>=|| than reference stat   
    counts = np.array([0,0,0]) # (lesser, greater)

    total_perms = bincoef(len(data), len(A))
    if not limit or total_perms < limit :
        limit = None
        comb_function = itertools.combinations
    else:
        comb_function = random_combination

    if progress_bar:
        progress_bar.max = limit or total_perms
        progress_bar.label = "of %d permutations" % progress_bar.max
    for binary_row in binary_combinations(len(data), len(A), comb_function=comb_function, limit=limit):
        #print binary_row
        stat_this = np.sum(np.array(data)*binary_row)
        counts = counts + stat_compare(stat_ref,stat_this)
        # if progress_bar:
        #    progress_bar.advance()

    # return p-values for lower, upper, and two-tail tests (FP number)
    n_comb = np.multiply.reduce(np.array(range(len(data)-len(A)+1,len(data)+1)))\
           / np.multiply.reduce(np.array(range(1,len(A)+1)))
    n_comb =  limit or total_perms
    counts[2] = min(2*counts[0:2].min(),n_comb) # hack to define p.twotail as 2*smaller of 1 tail p's
    return counts / float(n_comb)

def stat_compare(ref,test):
    """ Tests for comparing permutation and observed test statistics"""
    lesser = 1 * (test <= ref)
    greater = 1 * (test >= ref)
    more_extreme = 1 * (np.abs(test) >= np.abs(ref))
    return np.array([lesser,greater,more_extreme])
