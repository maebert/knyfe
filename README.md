
# What is knyfe?

knyfe is a python utility for rapid exploration of datasets. Use it when you have some kind of dataset and you want to get a feel for how it is composed, run some simple tests on it, or prepare it for further processing. The great thing about knyfe is that you don't have to know much about how your dataset is designed. You shouldn't have to remember in which variable resides in which column of your data matrix or how your structs are nested. Just get shit done.

## Native Datasets: JSON

Natively, knyfe treats data like JSON objects, or, key value pairs. If you know what JSON is, skip this section.

JSON knows essentially five kinds of stuff: 

* _Numbers_ (integer? float? who cares?), such as `42` and `1.618`
* _Strings_, such as `'spam'` and `"eggs"`
* _Arrays_ (or lists), such as `[23, 42, 3.14]` or `["pineapple", "lubricant"]` or `[17, "dwarves"]` (mixed data types? No problem!)
* _Booleans_, as in `true` and `false`
* _Objects_ (dict in Python), which are just `key: value`-pairs, such as `{name: 'luke', hands: 1, father: 'anakin'}`

Ah, and then there is `null`, which is equivalent to `None` in Python, and just means that there's a value missing (intentionally or unintentionally). How to make a dataset out of this? For our purposes, it's just a list of objects. Like this:

  [
    {
      species: 'Elephant',
      weight: 8014.2,
      age: 31
    },
    {
      species: 'Squirrel',
      weight: 0.021,
      age: .7
    }
  ]


A dataset is simply a list of data samples, and samples are nothing but
key-value pairs, or dictionaries. This class is a wrapper that allows you
to rapidly interact with these kind of data sets.

Storing your datasets as lists of key-value pairs has the advantage that we
can save them as JSON, or put them into a MongoDB. Let's assume we've got a
JSON object in the file mydata.json that looks roughly like this:

  [
    
    {
      name: "Jeanne D'Arc",
      gender: "female",
      continent: "Europe",
      age: 19
    
    },
    {

    }
  ]

- we can construct a Data object like this:

  data = Data("mydata.json")

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