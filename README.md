# WordNet simple API

An experimental API and basic front end exposing some of the word (synset) comparison features of the Wordnet NLTK corpus and associated Python interface.

## What this DOES do

 - It will allow determining meanings (synsets), and associated direct relationship synsets (hyponyms, hypernyms, holonyms, meronyms), for individual words (and a small selection of two part words that are effectively a single word). See `/synsets`
 - It will allow comparison of a pair of synsets (not words, because of potential meaning ambiguity) for words and a small selection of two part words that are effectively a single word. Comparison method can be chosen. A numeric score is returned. See `/synset_similarity` page.
 - It will allow comparison of two phrases by either a crude pairwise maximum synset similarity for each word in each phrase (*really* slow); or a 'cosine' method of phrase comparison (one objective calculation method of meaning similarity, but does not account for context). The phrase can be pre-processed to remove stopwords and/or stem the individual words. A numeric score is returned. See `/phrase_compare` page.
 - Two CLI utilities allow pre-processing of one or two TSV input files holding a term and definition of that term per row. The end result is a 'job' entry in the database (_displayed info needs improving_) and a large number of associated rows holding each pair of terms and asociated descriptive phrases and the computed comparison score for the comparison method chosen.
 
## What this DOES NOT do
 - specifically, it does not provide any indication of **phrase** relationship (other than a measure of similarity). Therefore, this cannot (at the moment) be used to determine ontological relationships *between phrases*.

## Starting
Example for Willow IP address.

[TO EXPAND]

 - ssh -> login as domain account (you may need perms on that box)
 - sudo to kai user
 - cd to ~/apis/wordnet
 - run >pipenv shell
 - then, from within the PIPENV, run python start.py -i 10.100.1.37 -p 8888 -n comparison.db

## User interface

The UI currently consists of four example pages using some of the below REST endpoints, and a homepage dispkaying example usages of the REST endpoints.
![image](https://user-images.githubusercontent.com/24891686/219006449-95a80371-9988-4190-8699-47985c848077.png)

### Synsets
http://127.0.0.1:8888/synsets

This is simply a nested list view mirroring the return JSON from the `/api/synsets` endpoint
![image](https://user-images.githubusercontent.com/24891686/219006705-c4556392-c37e-4279-8a9a-72d6b784222e.png)


#### Browse data

I implemented  browseable areas of the synset trees - 

##### Descendent synset(s) 

The synsets derectly related to the seed word

  - hypernyms (a word that is more generic than a given word), 
  - hyponyms (a word that is more specific than a given word), 
  - meronyms (a word that names a part of a larger whole) and 
  - holonyms (a word that names the whole of which a given word is a part)
 

[Definitions lifted from Wordnet...]
 
Each subordinate synset reloads the /synsets page with the new synset(s) displayed. [Try it with the above words.]

##### Individual root synset 

One of a set of root sibling synsets can be selected (NOTE: This doesn't show any more detail, but does use the alternate back-end synset retrieval by its name, rather than index - s probably a more reliable synset retrieval API endpoint)

##### Lemmas

The displayed lemmas of each synset are linkable, and will re-open the /synsets UI page with the selected lemma used as the seed word, thus allowing beowsing the synsets for this new word.

### Synset compare
http://127.0.0.1:8888/synset_similarity

This is a combination of retrieving synset summaries for a pair of words (`http://127.0.0.1:8888/api/synsets_pair_summary?word1=fish&word2=banana`), and a subsequent selection of two synsets to compare for similarity (`http://127.0.0.1:8888/api/synset_similarity_by_name?synset1=pisces.n.02&synset2=banana.n.02&comparison_type=wup`):

![image](https://user-images.githubusercontent.com/24891686/219007130-6c207a38-361d-4d1b-997f-8dcea3cc656a.png)

The final output requires more work I think.

### Phrase compare
This is a work in progress attempting to provide a similarity methodology for comparing phrases. Various references suggest this is very difficult or not possible using the Wordnet API (because it is word-based and context is hard to automatically determine). 

This iteration uses a crude comparison of each synset of each word in each phrase, and returns the highest comparison found. Stop words are removed and stemming is performed by default, with the option to not do so for either. 

#### Gotchas
 - sometimes, the UI shows that stemmed words don't actually exist in the database (such as 'cheese' -> 'chees' or 'deity' -> 'deiti'). Though note that the underlying API allows for different stemmer types and this may alter these results
 - sometimes, the stemming will result in a perfectly valid new word, that has no relationship in meaning to the root word: 'lathe' -> 'lath' is an example of this, where clearly one is a turning tool and the other is a type of walll building material... Unchecking the 'perform stemming' option may correct this.

Under both these circumstances, the phrase comparison will fail.

#### Enter phrases
Add the phrases to compare to the two text fields. There is a blur handler that triggers the pre-processing options currently set, and a preview is displayed under each textbox. Currently, the input phrases can be processed to remove stopwords and/or each word in the phrase can be stemmed:

![image](https://user-images.githubusercontent.com/24891686/219007597-3e1d8332-ca4f-4090-a48d-25e9b6705ffa.png)


Note that the **Comparison type** currently accepts 'pair-wise' or 'cosine' comparison methods. The underlying call to the API REST `/api/phrase_similarity` endpoint can accept URL parameters of `phrase_ct` (phrase comparison type) and `word_ct` (word comparison type). The latter is only relevant for pairwise comparison and both of these arguments default to values relevant for pair-wise phrase comparison. The model controller at the back end currently only handles this pairwise method, though also has (unused) arguments in preparation for alternative methods.

#### Compare phrases
Once the input phrases have been added, clicking the button will actually perform the comparison. The process is thus:

 - each word in processed phrase 1 is compared to each word in processed phrase 2
 - for each word pair, the synset(s) for each are obtained
 - for each **synset** pair a comparison is made, using the default synset comparison method of Wu-Palmer. Though please note that the back-end handler method will accept alternative word compare types.
 - The comparison score for each synset pair is tracked, and, if it is a higher score than currently held, this new higher score is noted, along with the synsets and associated words that resulted in this score.
 - finally, the comparison returns the highest similarity score of all the word -> synset pairs in the two phrases, along with the relevant word and synset pair

Note that in the following example, the resulting synsets are actually the same - this is because one of the synsets of 'chip' is in fact the same as one of the synsets for 'crisp':

![image](https://user-images.githubusercontent.com/24891686/215514891-8c35efcf-71e1-4134-b189-5be5b0b656c3.png)

So in this case, we get a 100% match.

An alternative example might be this:
![image](https://user-images.githubusercontent.com/24891686/215516071-453cab45-36cf-41c6-bcc8-9b372156a4b0.png)

Note that here, we don't have a 100% match, but a pretty good one (yes, backhoe is American English). In this case also, note that stemming is disabled, because the stem of 'backhoe' resulted in 'backho' - which did not exist.

The links will open views on the synset details for the word or synset selected. 

### Related phrases
This page allows the end user to submit a **term** (with autocomplete matching terms from the required **#job**) and a comparison threshold (_range 0 - 1 usually but may not be, depending on comparison method used. See later_). 

![image](https://user-images.githubusercontent.com/24891686/219009267-832319cc-67cb-4a8c-9255-1aaee57c823a.png)

Once a term and a comparison threshold has been selected, clicking the 'find related terms' button will return all entries in the database, for that job:

![image](https://user-images.githubusercontent.com/24891686/219011670-cb131f89-232f-4be6-bd21-15d6d0b02063.png)

Here, we have two similar (according to 'cosine' method) terms, based on the similarity of their descriptions.

## API Endpoints

### Synsets
`http://127.0.0.1:8888/api/synsets?word=jugs`

Get synsets for supplied word:

```json
{
	"source_word": "jugs",
	"synsets": [{
			"name": "jug.n.01",
			"definition": "a large bottle with a narrow mouth",
			"examples": [],
			"part_of_speech": "Noun",
			"lemmas": [
				"jug"
			],
			"hypernyms": [{
				"name": "bottle.n.01",
				"definition": "a glass or plastic vessel used for storing drinks or other liquids; typically cylindrical without handles and with a narrow neck that can be plugged or capped",
				"examples": [],
				"part_of_speech": "Noun",
				"lemmas": [
					"bottle"
				]
			}],
			"hyponyms": [{
					"name": "bellarmine.n.02",
					"definition": "a stoneware drinking jug with a long neck; decorated with a caricature of Cardinal Bellarmine (17th century)",
					"examples": [],
					"part_of_speech": "Noun",
					"lemmas": [
						"bellarmine",
						"longbeard",
						"long-beard",
						"greybeard"
					]
				},
				{
					"name": "water_jug.n.01",
					"definition": "a jug that holds water",
					"examples": [],
					"part_of_speech": "Noun",
					"lemmas": [
						"water_jug"
					]
				},
				{
					"name": "whiskey_jug.n.01",
					"definition": "a jug that contains whiskey",
					"examples": [],
					"part_of_speech": "Noun",
					"lemmas": [
						"whiskey_jug"
					]
				}
			]
		},
		{
			"name": "jug.n.02",
			"definition": "the quantity contained in a jug",
			"examples": [],
			"part_of_speech": "Noun",
			"lemmas": [
				"jug",
				"jugful"
			],
			"hypernyms": [{
				"name": "containerful.n.01",
				"definition": "the quantity that a container will hold",
				"examples": [],
				"part_of_speech": "Noun",
				"lemmas": [
					"containerful"
				]
			}],
			"hyponyms": []
		},
		{
			"name": "imprison.v.01",
			"definition": "lock up or confine, in or as in a jail",
			"examples": [
				"The suspects were imprisoned without trial",
				"the murderer was incarcerated for the rest of his life"
			],
			"part_of_speech": "Verb",
			"lemmas": [
				"imprison",
				"incarcerate",
				"lag",
				"immure",
				"put_behind_bars",
				"jail",
				"jug",
				"gaol",
				"put_away",
				"remand"
			],
			"hypernyms": [{
				"name": "confine.v.05",
				"definition": "deprive of freedom; take into confinement",
				"examples": [],
				"part_of_speech": "Verb",
				"lemmas": [
					"confine",
					"detain"
				]
			}],
			"hyponyms": []
		},
		{
			"name": "jug.v.02",
			"definition": "stew in an earthenware jug",
			"examples": [
				"jug the rabbit"
			],
			"part_of_speech": "Verb",
			"lemmas": [
				"jug"
			],
			"hypernyms": [{
				"name": "stew.v.03",
				"definition": "cook slowly and for a long time in liquid",
				"examples": [
					"Stew the vegetables in wine"
				],
				"part_of_speech": "Verb",
				"lemmas": [
					"stew"
				]
			}],
			"hyponyms": []
		}
	]
}
```

### Synset count
`http://127.0.0.1:8888/api/synset_count?word=jugs`

Get synset count for supplied word:

```json
{
  "status": "ok",
  "source_word": "jugs",
  "synset_count": 4
}
```

### Synset by name

return details, or summary, of a specified synset: 



#### detail
`http://10.100.1.37:8888/api/synset?synset_name=bottom-feeder.n.02`


```json
{
	"name": "bottom-feeder.n.02",
	"definition": "a fish that lives and feeds on the bottom of a body of water",
	"examples": [],
	"part_of_speech": "noun",
	"lemmas": [
		"bottom-feeder",
		"bottom-dweller"
	],
	"hypernyms": [{
		"name": "fish.n.01",
		"definition": "any of various mostly cold-blooded aquatic vertebrates usually having scales and breathing through gills",
		"examples": [
			"the shark is a large fish",
			"in the living room there was a tank of colorful fish"
		],
		"part_of_speech": "noun",
		"lemmas": [
			"fish"
		]
	}],
	"hyponyms": [{
		"name": "mullet.n.03",
		"definition": "bottom dwelling marine warm water fishes with two barbels on the chin",
		"examples": [],
		"part_of_speech": "noun",
		"lemmas": [
			"mullet"
		]
	}],
	"meronyms": [],
	"holonyms": []
}
```

#### Summary
`http://10.100.1.37:8888/api/synset?synset_name=bottom-feeder.n.02&summary=yes`


```json
{
  "name": "bottom-feeder.n.02",
  "definition": "a fish that lives and feeds on the bottom of a body of water",
  "examples": [],
  "part_of_speech": "noun",
  "lemmas": [
    "bottom-feeder",
    "bottom-dweller"
  ]
}
```

### Synsets summary for a pair of words
`http://127.0.0.1:8888/api/synsets_pair_summary?word1=fish&word2=sausage` 

Return a summary of each synset for a pair of words.

```json
{
	"status": "ok",
	"synset1": {
		"source_word": "fish",
		"synsets": [{
				"name": "fish.n.01",
				"definition": "any of various mostly cold-blooded aquatic vertebrates usually having scales and breathing through gills",
				"examples": [
					"the shark is a large fish",
					"in the living room there was a tank of colorful fish"
				],
				"part_of_speech": "noun",
				"lemmas": [
					"fish"
				]
			},
			{
				"name": "fish.n.02",
				"definition": "the flesh of fish used as food",
				"examples": [
					"in Japan most fish is eaten raw",
					"after the scare about foot-and-mouth disease a lot of people started eating fish instead of meat",
					"they have a chef who specializes in fish"
				],
				"part_of_speech": "noun",
				"lemmas": [
					"fish"
				]
			},
			{
				"name": "pisces.n.02",
				"definition": "(astrology) a person who is born while the sun is in Pisces",
				"examples": [],
				"part_of_speech": "noun",
				"lemmas": [
					"Pisces",
					"Fish"
				]
			},
			{
				"name": "pisces.n.01",
				"definition": "the twelfth sign of the zodiac; the sun is in this sign from about February 19 to March 20",
				"examples": [],
				"part_of_speech": "noun",
				"lemmas": [
					"Pisces",
					"Pisces_the_Fishes",
					"Fish"
				]
			},
			{
				"name": "fish.v.01",
				"definition": "seek indirectly",
				"examples": [
					"fish for compliments"
				],
				"part_of_speech": "verb",
				"lemmas": [
					"fish",
					"angle"
				]
			},
			{
				"name": "fish.v.02",
				"definition": "catch or try to catch fish or shellfish",
				"examples": [
					"I like to go fishing on weekends"
				],
				"part_of_speech": "verb",
				"lemmas": [
					"fish"
				]
			}
		]
	},
	"synset2": {
		"source_word": "sausage",
		"synsets": [{
				"name": "sausage.n.01",
				"definition": "highly seasoned minced meat stuffed in casings",
				"examples": [],
				"part_of_speech": "noun",
				"lemmas": [
					"sausage"
				]
			},
			{
				"name": "blimp.n.02",
				"definition": "a small nonrigid airship used for observation or as a barrage balloon",
				"examples": [],
				"part_of_speech": "noun",
				"lemmas": [
					"blimp",
					"sausage_balloon",
					"sausage"
				]
			}
		]
	}
}
```


### Compare two synsets (detail)
`http://127.0.0.1:8888/api/synset_similarity?word1=foundry&word2=ironworks&comparison_type=wup`

Compare two synsets for similarity.

 - required args are `word1` and `word2`, from which the synsets are obtained
 - option args are:
   - `index1`, `index2` - (an int). These indicate which synset for a given word should be used for the comparison. This allows the SAME word to have its different synsets compared. These both default to zero (i.e. the first synset for a word)
   - `comparison_type` (string of `path` (default), `wup` or `lch`) 


```json
{
	"source_word_1": "jugs",
	"source_word_2": "jugs",
	"comparison_type": "Wu-Palmer",
	"synset1": {
		"name": "jug.n.01",
		"definition": "a large bottle with a narrow mouth",
		"examples": [],
		"part_of_speech": "Noun",
		"lemmas": [
			"jug"
		]
	},
	"synset2": {
		"name": "jug.n.02",
		"definition": "the quantity contained in a jug",
		"examples": [],
		"part_of_speech": "Noun",
		"lemmas": [
			"jug",
			"jugful"
		]
	},
	"similarity": 0.125
}
```
Note that the compared pair can be (different) synsets from the same input word. Comparing two identical synsets is possible.   

### Compare synsets by name (detail)
`http://127.0.0.1:8888/api/synset_similarity_by_name?synset1=shark.n.01&synset2=shark.n.01&comparison_type=lch`

Compare two synsets by the canonical name of each synset. This is a better version of the above, tha does not rely on the array index being passed to identify which synset to use for comparison.

- required args are `synset1` and `synset2`
- optional arg is `comparison_type`, with a value of `wup` (Wu-Palmer, default), `lch` (Leacock-Chodorow) or `path` (Path distance)

```json
{
	"comparison_type": "Leacock-Chodorow",
	"synset1": {
		"name": "shark.n.01",
		"definition": "any of numerous elongate mostly marine carnivorous fishes with heterocercal caudal fins and tough skin covered with small toothlike scales",
		"examples": [],
		"part_of_speech": "noun",
		"lemmas": [
			"shark"
		]
	},
	"synset2": {
		"name": "shark.n.01",
		"definition": "any of numerous elongate mostly marine carnivorous fishes with heterocercal caudal fins and tough skin covered with small toothlike scales",
		"examples": [],
		"part_of_speech": "noun",
		"lemmas": [
			"shark"
		]
	},
	"similarity": 3.6375861597263857
}
```

### Compare phrases

Return phrase similarity. 

This currently provides a crude comparison of greatest synset similarity of any pair of words from each phrase or a 'cosine' comparison of the supplied phrases directly. 

The crude comparison assumes the input has already been processed for stopwords and stemming. An optional argument of 'word_ct' (word comparison type) can be passed, indicating the synset similarity method to use, defaulting to `wup` (Wu-Palmer) and allowing `lch` (Leacock-Chodorow) or `path` as well. There is crude error handling for mismatched 'part of speech' if Leacock-Chodorow method is used. 

The 'cosine' similarity calculation does not use the Wordnet synset comparison, but an implementation of Cosine Similarity (see https://newscatcherapi.com/blog/ultimate-guide-to-text-similarity-with-python for details). I ended up using an adaptation of a method provided by Mariusz, because the specific code example didn't work. 

The cosime method appears to work better on the unmodified phrase and as such, the UI should be set accordingly (no stemming, don't remove stopwords) 

The return structure is similar, but less complex, and is considerably faster.

#### Crude comparison examples
`http://127.0.0.1:8888/api/phrase_similarity?p1=bob%20builder&p2=pete%20gardener`

results in

```json
{
	"phrase1": [
		"bob",
		"builder"
	],
	"phrase2": [
		"pete",
		"gardener"
	],
	"phrase_comparison_type": "pairwise",
	"word_comparison_type": "wup",
	"result": {
		"calculated_similarity": 0.631578947368421,
		"synsets": [{
				"synset": {
					"name": "builder.n.02",
					"definition": "a person who creates a business or who organizes and develops a country",
					"examples": [
						"empire builder"
					],
					"part_of_speech": "noun",
					"lemmas": [
						"builder"
					]
				},
				"root_word": "builder"
			},
			{
				"synset": {
					"name": "gardener.n.01",
					"definition": "someone who takes care of a garden",
					"examples": [],
					"part_of_speech": "noun",
					"lemmas": [
						"gardener",
						"nurseryman"
					]
				},
				"root_word": "gardener"
			}
		]
	},
	"status": "ok",
	"message": "processing completed"
}
```

`http://127.0.0.1:8888/api/phrase_similarity?p1=bob%20builder&p2=pete%20gardener&word_ct=lch`

results in an error

```json
{
	"phrase1": [
		"bob",
		"builder"
	],
	"phrase2": [
		"pete",
		"gardener"
	],
	"phrase_comparison_type": "pairwise",
	"word_comparison_type": "lch",
	"result": {},
	"status": "error",
	"message": "Computing the lch similarity requires Synset('bob.v.01') and Synset('gardener.n.01') to have the same part of speech."
}
```
#### Cosine comparison example
`http://127.0.0.1:8888/api/phrase_similarity?p1=GDP%20is%20the%20sum%20of%20all%20goods%20and%20services%20produced%20in%20the%20country%E2%80%99s%20economy.%20If%20it%20is%20up%20on%20the%20previous%20three%20months%20the%20economy%20is%20growing.%20If%20GDP%20is%20down%20the%20economy%20is%20contracting.&p2=GNP%20is%20another%20way%20to%20measure%20the%20economy%20but%20also%20the%20welfare%20of%20British%20citizens.%20This%20is%20GDP%20plus%20the%20profits%20interest%20and%20dividends%20received%20from%20British%20residents%20abroad%20and%20minus%20those%20profits%20interest%20and%20dividends%20paid%20from%20the%20UK%20to%20overseas%20residents.&phrase_ct=cos`

```json
{
	"phrase1": "GDP is the sum of all goods and services produced in the country’s economy. If it is up on the previous three months the economy is growing. If GDP is down the economy is contracting.",
	"phrase2": "GNP is another way to measure the economy but also the welfare of British citizens. This is GDP plus the profits interest and dividends received from British residents abroad and minus those profits interest and dividends paid from the UK to overseas residents.",
	"phrase_comparison_type": "cos",
	"word_comparison_type": "wup",
	"result": {
		"status": "ok",
		"message": "ok",
		"calculated_similarity": 0.34697450329048424
	},
	"status": "ok",
	"message": "ok"
}
```

### Stemmer
`http://127.0.0.1:8888/api/word_stem?word=denies&stemmer=sp`

return word stem for supplied word, with three possible stemming algorithms.

 - required arg is `word` - the word to stem
 - optional arg is `stemmer` - indicate which stemmer algorithm to use. One of `se` (default), `po` or `sp`


```json
{
  "source_word": "denies",
  "stemmed_word": "deni",
  "stemmer_key": "sp",
  "stemmer_name": "Snowball (Porter)"
}
```

### Check for stop word
`http://127.0.0.1:8888/api/is_stop_word?word=fishing`

Returns boolean depending on whether the supplied word is in the NLTK stopword list.

See [https://pythonspot.com/nltk-stop-words/](https://pythonspot.com/nltk-stop-words/) for pre-usage setup.

 - required arg is `word` - the word to analyse
 
if it **is** a stopword:

```json
{
  "status": "ok",
  "word": "and",
  "is_stop_word": true
}
```


if **not** a stopword:

```json
{
  "status": "ok",
  "word": "fishing",
  "is_stop_word": false
}
```

### Process a list of input words
`http://127.0.0.1:8888/api/get_processed_list?words=fishing,and,haddocks,with,groupers,having,sharklike&remove_stopwords=falsed&perform_stem=sdcvfwrf&stemmer=po`

Returns a structure mapping input word list to processed output word list, by: 
 - no action (i.e the raw input list is returned)
 - stemming (each word in the list is stemmed with default stemmer)
 - optionally by specified stem method and/or stopword removal 

URL parameters are:
 - required arg is `words` - a comma separated list of input words
 - optional `remove_stopwords` arg, defaulting to `true`
 - optional `perform_stemming` arg, defaulting to `true`
 - optional stemming method, `stemmer`, defaulting to `se` (Snowball (English))

```json
{
	"source_data": [
		"fishing",
		"and",
		"haddocks",
		"with",
		"groupers",
		"having",
		"sharklike"
	],
	"perform_stem": true,
	"processed_list": [{
			"source_word": "fishing",
			"stemmed_word": "fish",
			"stemmer_key": "po",
			"stemmer_name": "Porter"
		},
		{
			"source_word": "haddocks",
			"stemmed_word": "haddock",
			"stemmer_key": "po",
			"stemmer_name": "Porter"
		},
		{
			"source_word": "groupers",
			"stemmed_word": "grouper",
			"stemmer_key": "po",
			"stemmer_name": "Porter"
		},
		{
			"source_word": "sharklike",
			"stemmed_word": "sharklik",
			"stemmer_key": "po",
			"stemmer_name": "Porter"
		}
	]
}
```
# CLI Tools

Currently, two test CLI tools are available -

`synonimize.py` and `synonimize2.py`

These both analyse lists of terms and associated descriptive phrases for similarity, based on simplistic phrase comparison methods. 

The first uses a single input file and can use either a highest-word-similarity approach, a `cosine` or a 'Roberta' phrase similarity (TODO: ref here). 

The second uses two input files rather than one.

NOTE: The second CLI tool is limited to two input files, and therefore will be problematic to use for multiple sources. Therefore, it is suggested that the first `synonimize.py` CLI too is used, but with an input file PRE-PROCESSED to be a combination of multiple sources. This will of course require some pre-processing of the various data sources to align the data fields. (see https://github.com/Kaiasm/apis/issues/23).


[Note that for both, plugging in other comparison methods should be possible, though that would depend on the back-end knowing about alternate comparison methods, which at the moment it does not]

## Expected input format

Both tools expect input files to be TSV files, with the following basic structure:
 - The columns to use can be specified as CLI args, so it doesn't matter if there are extra columns with irrelevant data
 - One must be the term being described
 - one must be the description of that term

e.g., for `file1.tsv`

```
column 1 heading	column 2 heading	column 3 heading	column 4 heading						column n heading
item type 27		laser printer		in the office		thing for printing using laser technology and loads of carbon	last updated by bob t. builder
...
```

and `file2.tsv`

```
column 1 heading	column 2 heading					column 3 heading	column 4 heading	column n heading
printers (laser)	asset of type laser printer, requires toner		foyer, lobby #2		£1,000 - £1,999		some other arbitrary attribute
...
```

We can therefore specify the command-line like so, 

`~/deploy/apis/wordnet/synonimize2.py -f /path/to/file1.tsv -g /path/to/file2.tsv -t 2 -u 1 -d 4 -e 2 -r 4 -s 2 -c 0.0 -n fish.db`

where:

 - `-f`, `-g`: full paths to input TSV file
 - `-t`, `-u`: columns holding the terms
 - `-d`, `-e`: columns holding data to analyse for similarity. Note this is separate from the fields specified below because it may be that a display descriptive string and the phrase to actually analyse are in different columns 
 - `-r`, `-s`: columns holding descriptions of the terms, not processed for display purposes only
 - `-c`: threshold value. phrase pairs returning a comparison value less than this will not be recorded (may need to change - see notes on API endpoint TODO: REF!)
 - `-n`: database name. Optional, will default to `comparison.db` 
 - `-m`: phrase comparison method to use. Optional. One of `pw` (default),`cos`,`tf` at the moment. More can be added once they are developed.

Note the correlation between the CLI args and the columns in the input with the expected locations of the input data.

## Multiple data sources

Where there are multiple sources of data to synonimize, I suggest that this can be accomplished like so (see https://github.com/Kaiasm/apis/issues/23):

 - A preliminary task of combining the data (spreadsheet, database, PDFs or whatever) that describe the entities from each department needs to be combined to a single TSV that includes at least:
   - the term
   - the description of that term
   - originating department
 - The existing CLI tool for single spreadsheet analysis can be used, with suitable modifications to account for department field as well (this will have no bearing on the analysis itself, but will be carried through to the database, so we have a record of whcih departments hold synonymous descriptions)
 - The output database will include the departments found for each term compared
   - suitable queries will be needed to account for these

# Other info
## setup notes (updated)

The wordnet tool has a PIPNEV for dependency management. Therefore, the target machine must have pipenv installed.

### PIPENV setup
The setup should now be a case of pulling the repo, and installing the dependencies in the pipfile:

`>pipenv install`

This will deploy all the requirements in the new PIPENV. The, run the utility from the PIPENV:

`> pipenv shell`

`(wordnet)~path/to/apis/wordnet$ python start.py  -i 10.100.1.37 -p 8888` (e.g.)


### (manual) Wordnet
The main pre-requisite is to install the wordnet NLTK resource:

You may well see an error like so:

```
  File "/home/silasj@grange.taxonomics.co.uk/.local/lib/python3.8/site-packages/nltk/corpus/util.py", line 84, in __load
    root = nltk.data.find(f"{self.subdir}/{zip_name}")
  File "/home/silasj@grange.taxonomics.co.uk/.local/lib/python3.8/site-packages/nltk/data.py", line 583, in find
    raise LookupError(resource_not_found)
LookupError: 
  Resource wordnet not found.
  Please use the NLTK Downloader to obtain the resource:
```



if you run the code without the wordnet NLTK extension (corpus).

There are many references - e.g.:

https://www.nltk.org/data.html
https://stackoverflow.com/questions/6661108/import-wordnet-in-nltk
...

Basically, we need the Wordnet database, though there are a couple of things I found.

From a Python shell:

```
>>> import nltk
>>> nltk.download('wordnet')
[nltk_data] Downloading package wordnet to
[nltk_data]     /home/silasj@grange.taxonomics.co.uk/nltk_data...
True
>>> from nltk.corpus import wordnet as wn
>>> wn.synsets('haddock')
Traceback (most recent call last):
  File "/home/silasj@grange.taxonomics.co.uk/.local/lib/python3.8/site-packages/nltk/corpus/util.py", line 84, in __load
    root = nltk.data.find(f"{self.subdir}/{zip_name}")
  File "/home/silasj@grange.taxonomics.co.uk/.local/lib/python3.8/site-packages/nltk/data.py", line 583, in find
    raise LookupError(resource_not_found)
LookupError: 
**********************************************************************
  Resource omw-1.4 not found.
  Please use the NLTK Downloader to obtain the resource:

  >>> import nltk
  >>> nltk.download('omw-1.4')
```

So it turns out I also needed the `omw-1.4` package too:

```
>>> nltk.download('omw-1.4')
[nltk_data] Downloading package omw-1.4 to
[nltk_data]     /home/silasj@grange.taxonomics.co.uk/nltk_data...
True
>>> wn.synsets('haddock')
[Synset('haddock.n.01'), Synset('haddock.n.02')]
```

I did need to try a couple of times to set this up, but the texts returned by the errors prior to installing the corpus and additional resource was helphul and allowed me to get going pretty quick.

### `spacy` - for phrase comparison (likely not relevant any more)
~~this (https://newscatcherapi.com/blog/ultimate-guide-to-text-similarity-with-python) suggested spaCy package:

~~`pip install -U spacy`

~~Set up required data:

~~`python3 -m spacy download en_core_web_md` 

### scikit-learn
But I had problems getting the example working, so I used the sklearn packages instead:

[https://scikit-learn.org/stable/](https://scikit-learn.org/stable/)

```python
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
```
And this seemed to be successful.

## 'SpaCy' is superceded by this:
TODO: describe reliminary actions for `Roberta` phrase comparison. Essntially, PIPENV install/update (for required libs) and a huge data set on first calling the libraries (about 1.5GB)

pre-reqs for 'roberta' model
 - pipenv install sentence_transformers 
 

remote updated
 
updates: 
pipenv install sentence_transformers 

## Usage
There are plenty of references on how to use the wordnet corpus, but essentially, the way in is via the `synsets` list attached to each root word.


## refs

In no particular order (to sort out)

### NLTK setup
https://stackoverflow.com/questions/6661108/import-wordnet-in-nltk (adding corpus)
https://www.nltk.org/data.html (adding corpus)

### Python usage
https://www.nltk.org/howto/wordnet.html
https://www.nltk.org/api/nltk.corpus.reader.wordnet.html (examples/API)
https://www.nltk.org/_modules/nltk/corpus/reader/wordnet.html
https://pythonprogramming.net/wordnet-nltk-tutorial/
https://www.educative.io/answers/how-to-use-wordnet-in-python
https://www.geeksforgeeks.org/nlp-synsets-for-a-word-in-wordnet/
https://www.guru99.com/wordnet-nltk.html




## Code deployment and running

 - pull APIs repo (`https://github.com/Kaiasm/apis.git`)
 - in the `apis/wordnet/` directory, run `start.py` with suitable IP and port:
   - `python start.py -i 127.0.0.1 -p 8888`
 - The current state is some REST endpoints, summarised on the main homepage, that accept GET URL attributes and return data and a simple set of UI pages available form the root at the specified port and IP address.
 - Please note the optional argument of `-n`, specifying a SQLite database name to store comparison data in can be used. This defaults to `comparison.db`



## TODOs
 - Custom exception(s)
 - UI/template(s)
 - new REST module for template rendering, on separate namespace to API 






