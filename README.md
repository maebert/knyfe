What is knyfe?
==============

knyfe is a python utility for rapid exploration of datasets. Use it when you have some kind of dataset and you want to get a feel for how it is composed, run some simple tests on it, or prepare it for further processing. The great thing about knyfe is that you don't have to know much about how your dataset is designed. You shouldn't have to remember in which variable resides in which column of your data matrix or how your structs are nested. Just get shit done.

Quickstart
----------

    cereals = knyfe.Data("examples/cereals.data")
    print cereals.summary


Native Datasets: JSON
---------------------

Natively, knyfe treats data like JSON objects, or, key value pairs. If you know what JSON is, skip this section.

### Why JSON?

Any data format should be constructed after three principles:

1. Human readable
2. Explict (ie. self-contained)
3. Flexible

In other words, a dataset shouldn't look like this: `PK\x03\x04\x14\x00\x00\x00\x00\x00\xce\xad` and it also shouldn't look like `5.1,3.5,1.4,0.2;4.6,3.1,1.5,0.2`. Why? For two reasons:

1. If other people want to use your data, the should know what they're dealing with.
2. Human readable means anybody will be able to open the data set, now and in 50 years.

### What does JSON look like?

If you know Python, JSON will look very familiar: it translates to Python `dict` and `list` types almost directly. The only difference is that `None` in Python is `null` in JSON, and keys don't have to be strings. So a Dataset in JSON may look like this:

  [
    {
      species: 'Elephant',
      weight: 8014.2,
      age: 31,
      name: 'Dumbo'
    },
    {
      species: 'Squirrel',
      weight: 0.021,
      age: .7,
      name: null
    }
  ]

Now let's play around a bit:

  data = data.filter(gender='male', continent=('Europe', 'Asia')).get('age')

Will return a numpy array containing the ages of all dudes living in Europe
or Asia. Notice the method chaining; filter (and other methods like it) will
always return a new Data object. Want some statistics:

  data.filter(lambda d: squeeze(d) == "quiek").mean('size', 'weight')

gives you the mean size and weight of all samples that make "quiek" when
squeezed (ie. all key-value-pairs that return "quiek" when passed to the
squeeze function). If we're often interested in the same variables, we can set

    data.set_dependent('size', 'weight')

and now just call data.mean() to get the mean size and weight.

But hey, let's get serious and run a proper test:

    data.set_dependent('awesomeness')
    ninjas = data.filter(job='ninja').remove_outliers()
    pirates = data.filter(job='pirate').remove_outliers()
    ninja.permutation_test(pirates)

Will first construct datasets with only ninjas and pirates, respectively,
remove the super awesome and super lame from each group, and then run a
permutation test to see whether the dependent variable (awesomeness) is
significantly different in these two groups. The great thing about 
permutation tests is that you need to know almost nothing about your 
distribution. It's the most take-no-prisoners kind of statistical test there
is. And it will give you a p value. Less is more. e.g. a p-value of 0.04 will
tell you that there's a 96%% chance that these groups really differ in
awesomeness and it's not just random fluctuation that makes for different mean
values.