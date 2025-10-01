 /**
 * 
 */

let engine = {
	
	comparisonTypeMapper : {
		'pw' : 'Pairwise',
		'cos' : 'Cosine',
		'tf' : 'Tensorflow',
		'rb' : 'Roberta'
	},
	
	init : function(){
		 
		let context = document.getElementsByTagName('body')[0].getAttribute('data-js-context');
		// console.log('startup', context);
		switch(context){
			case 'index':
				// console.log('do homepage stuff');
				break;
			case 'synsets':
				// console.log('do synset stuff');
				this.init_synsets();
				break;
			case 'synset_similarity':
				// console.log('compare synsets');
				this.init_synset_similarity();
				break;
			case 'phrase_compare':
				console.log('case compare phrases');
				this.init_phrase_compare();
				break;
			case 'get_related_phrases':
				console.log('case compare phrases');
				this.init_get_related_phrases();
				break;
					 
		}
	},
	 
	init_synsets : function(){
		/** add handler to button */
		document.getElementById('go').addEventListener('click',engine.getSynsets);
		
		/** handle URL parameters, synsets */
		if(this._getQSVal(document.location,'word')){
			document.getElementById('root_word').value = this._getQSVal(document.location,'word');
			document.getElementById('go').click();
		}
		
		if(this._getQSVal(document.location,'synset_name')){
			/** do AJAX query for individual synset name */
			// console.log(this._getQSVal(document.location,'synset_name'));
			this.getSynset(this._getQSVal(document.location,'synset_name'));
		}
	},
	
	init_synset_similarity : function(){
		/** add handler to synset lists button */
		document.getElementById('go').addEventListener('click',engine.getSynsetsComparisonLists);
		
		/** add handler to compare button */
		document.getElementById('compare').addEventListener('click',engine.compareSelectedSynsets);
		
		
		/** handle URL parameters, synset_comparison, initial quiery for synsets of word pair */
		if(this._getQSVal(document.location,'word1') && this._getQSVal(document.location,'word2')){
			document.getElementById('word1').value = this._getQSVal(document.location,'word1');
			document.getElementById('word2').value = this._getQSVal(document.location,'word2');
			// document.getElementById('comparison_type').value = this._getQSVal(document.location,'comparison_type');
			document.getElementById('go').click(); 
		}
	},
	
	init_phrase_compare : function(){
		console.log('start init_phrase_compare')
		/** add handlers to buttons: */
		let destop = document.getElementById('destop');
		destop.addEventListener('click',engine.preProcessPhrases);
		
		/** add handler to stemming checkbox */
		let stemmers = document.getElementById('perform_stem').addEventListener('click',engine.toggleStemmerVisibility);
		
		/** blur handlers to auto-process the lists */
		document.getElementById('p1').addEventListener('blur',engine.handlePhraseBlur);
		document.getElementById('p2').addEventListener('blur',engine.handlePhraseBlur);
		document.getElementById('remove_stopwords').addEventListener('click',engine.stopwordsCheckboxHandler)
		
		/** attach handlers to the stemmer types radio buttons  */
		let stemmer_types = document.querySelectorAll('#stemmer_types > input[type="radio"]');
		for(entry of stemmer_types){
			entry.addEventListener('click',engine.stemmerTypesHandler)
		}
		
		/** and trigger the first load */
		//document.getElementById('destop').click();
		console.log('appending click handler')
		document.getElementById('compare').addEventListener('click',engine.comparePhrases);
	},
	
		
	init_get_related_phrases : function(){
		console.log('getting comparison jobs list...')
		/** first we need to get all jobs for the currently selected database */
		this.getJobList(document.getElementById('job_list')); //will paginate eventually perhaps???
		
		/** text box handler */
		document.getElementById('term').addEventListener('keyup',engine.getFilteredTerms);			//SQL filter for terms, autopopulate an array
		
		/** button handler */
		document.getElementById('find_related').addEventListener('click',engine.getRelatedTerms);	//Trigger the request to return the relted terms based on the chosen term
		
		document.getElementById('comparison_threshold').addEventListener('keyup',engine.handleThresholdKeyUp);
		//document.getElementById('comparison_threshold').addEventListener('blur',engine.getTemporaryAutocompletePhraseData);
		
	},
	
	/** pass data to  */
	getRelatedTerms : function(){
		document.querySelector('#find_related_spinner > img').classList.remove('hidden');
		/** https://stackoverflow.com/questions/9618504/how-to-get-the-selected-radio-button-s-value - I have a blind-spot about this syntax!*/
		let job_uuid = document.querySelector('input[name="job_uuid"]:checked').value;
		let term = document.getElementById('term').value;
		let limit = document.getElementById('comparison_threshold').value;
		let comp_type = document.getElementById('selected_job_comparison_type').value;
		let endpoint = '/api/get_similar_terms?job_uuid='+job_uuid+'&term='+term+'&limit=' + limit + '&comparison_type=' + comp_type;
		fetch(endpoint)
			.then( response => response.json() ) //This doesn't like being multi-line. Don't know why...
			.then(function(data){
				console.log(data);
				let target = document.getElementById('output');
				target.innerHTML = '';
				let _table = engine.getTag('table');
				let _ul = engine.getTag('ul');
				for(datum of data){
					let _tr = engine.getTag('tr');	//TODO: Need to get TH etc. here really
					let _li = engine.getTag('li');
					_li.appendChild(document.createTextNode(datum['TERM_1']+"/"+datum['TERM_2'] +" - "+datum['COMPARISON_SCORE']));
					_ul.appendChild(_li);
					
					let _td1 = engine.getTag('td');
					let _td2 = engine.getTag('td');
					let _td3 = engine.getTag('td');
					let _td4 = engine.getTag('td');
					let _td5 = engine.getTag('td');
					
					_td1.appendChild(document.createTextNode(datum['TERM_1']));
					_td2.appendChild(document.createTextNode(datum['DESCRIPTION_1']));
					_td3.appendChild(document.createTextNode(datum['TERM_2']));
					_td4.appendChild(document.createTextNode(datum['DESCRIPTION_2']));
					_td5.appendChild(document.createTextNode(datum['COMPARISON_SCORE']));
					
					_tr.appendChild(_td1);
					_tr.appendChild(_td2);
					_tr.appendChild(_td3);
					_tr.appendChild(_td4);
					_tr.appendChild(_td5);
					_table.appendChild(_tr);
				}
				//target.appendChild(_ul);
				document.querySelector('#find_related_spinner > img').classList.add('hidden');
				target.appendChild(_table);
			});
	},
	
	getJobList : function(target){
		/** show the spinner */
		document.querySelector('#load_jobs_spinner > img').classList.remove('hidden');
		
		let endpoint = '/api/get_jobs';
		/** using fetch() api: https://developer.mozilla.org/en-US/docs/Web/API/Fetch_API/Using_Fetch */
		fetch(endpoint)
			.then( response => response.json() ) //This doesn't like being multi-line. Don't know why (curly braces?)...
			.then(function(data){
//				let counter = 1;
//				let _ul = engine.getTag('ul');
				
				let _table = engine.getTag('table');
				let _thead = engine.getTag('thead');
				let _trhead = engine.getTag('tr');
				let _th1 = engine.getTag('th');
				let _th2 = engine.getTag('th');
				let _th3 = engine.getTag('th');
				let _th4 = engine.getTag('th');
				
				_th1.appendChild(document.createTextNode('JOB'));
				_th2.appendChild(document.createTextNode('METHOD'));
				_th3.appendChild(document.createTextNode('PROCESSING SCRIPT'));
				_th4.appendChild(document.createTextNode('RANGE'));
				
				_trhead.appendChild(_th1);
				_trhead.appendChild(_th2);
				_trhead.appendChild(_th3);
				_trhead.appendChild(_th4);
				_thead.appendChild(_trhead);
				_table.appendChild(_thead);
				
				for(datum of data){
					console.log(datum);
					let _tr = engine.getTag('tr');
					let _td1 = engine.getTag('td');
					let _td2 = engine.getTag('td');
					let _td3 = engine.getTag('td');
					let _td4 = engine.getTag('td');
					
					// build tag attributes:
					let current_attrs = [['type','radio'],['name','job_uuid'],['value',datum['job_uuid']],['data-comparison-type',datum['comparison_type']]]
//					console.log(datum['min'], parseFloat(datum['min']), datum['max'], parseFloat(datum['max']) )
					// see https://stackoverflow.com/questions/22600248/is-nan-falsy-why-nan-false-returns-false
					if(datum['min'] && datum['max'] && parseFloat(datum['min']) && parseFloat(datum['max'])){
						console.log('appending range data')
						current_attrs = current_attrs.concat([['min',datum['min']], ['max',datum['max']] ])
						
						//show comparison range
						_td4.appendChild(document.createTextNode(datum['min'] +' to '+ datum['max']));
					}
					
					let _radio = engine.getTag('input',current_attrs);
					_radio.addEventListener('click',engine.relatedPhraseJobClickHandler)
//					let _li = engine.getTag('li');
//					_li.appendChild(_radio);
//					_li.appendChild(document.createTextNode('job# ' + counter + ' ' + engine.comparisonTypeMapper[datum['comparison_type']] + ' (using ' + datum['processor'] +')' ));
//					_ul.appendChild(_li);
					
					_td1.appendChild(_radio);
					_td1.appendChild(document.createTextNode('job# '+ datum['job_uuid']));
					_td2.appendChild(document.createTextNode(engine.comparisonTypeMapper[datum['comparison_type']]));
					_td3.appendChild(document.createTextNode(datum['processor']));					

					_tr.appendChild(_td1);
					_tr.appendChild(_td2);
					_tr.appendChild(_td3);
					_tr.appendChild(_td4);
					
					_table.appendChild(_tr);
//					counter++;
				}
				console.log(_table)
				// first_li = _ul.querySelector('li:nth-of-type(1) > input');
				first_li = _table.querySelector('tr:nth-of-type(1) > td >  input');
				first_li.setAttribute('checked','checked');
//				target.appendChild(_ul);
				target.appendChild(_table);
				
				let rads = document.getElementsByName('job_uuid');
//				console.log(rads);
//				console.log(rads.length);
				for(let a=0; a < rads.length; a++){
					let item = rads[a];
//					console.log(typeof(item))
//					console.log(a)
//					console.log(rads[a]);
				};
				
				/** show the spinner */
				document.querySelector('#load_jobs_spinner > img').classList.add('hidden');
				
			})
	},

	/** retrieve synset(s) for given word */
	getSynsets : function(){
		/** get the word in the text box. Note there are some short phrases as lemmas already in the database, with spaces replaced with underscores. */
		let root_word = document.getElementById('root_word').value.replace(/ /g,'_');
		
		/** we need to ensure the URL reflects what is in the box: */
		window.history.replaceState(null,'gish','/synsets?word=' + document.getElementById('root_word').value);
		
		// console.log('get synsets for',root_word ,'...');
		document.querySelector('#get_synsets_spinner > img').classList.remove('hidden')
		let endpoint = '/api/synsets?word='+root_word;
		/** using fetch() api: https://developer.mozilla.org/en-US/docs/Web/API/Fetch_API/Using_Fetch */
		fetch(endpoint)
			.then( response => response.json() ) //This doesn't like being multi-line. Don't know why...
			.then(function(data){
				console.log('response',data);
				let _ul = engine.getTag('ul',[['class','synsets'],['id','test']]);
			 
				/** build DOM outputs */
				for(synset of data.synsets){
					let _liSynset = engine.getSynsetDOMTree(synset);
					_ul.appendChild(_liSynset);
				}
			 
				let target = document.getElementById('results');
				target.innerHTML = '';
				target.appendChild(_ul);
				//and hide the spinner:
				document.querySelector('#get_synsets_spinner > img').classList.add('hidden')
				// console.log(_ul)
			}
			)
	},
	
	/** retrieve synset for given synset name */
	getSynset : function(synset_name){	
		let endpoint = '/api/synsets?synset_name='+synset_name;
		
		/** using fetch() api: https://developer.mozilla.org/en-US/docs/Web/API/Fetch_API/Using_Fetch */
		fetch(endpoint).then((response) => response.json()).then(function(data){
			let _ul = engine.getTag('ul',[['class','synsets'],['id','test']]);
			let _liSynset = engine.getSynsetDOMTree(data); 
			_ul.appendChild(_liSynset);
			let target = document.getElementById('results');
			target.innerHTML = '';
			target.appendChild(_ul);
			// console.log(_ul);
		})
	},	
	
	getSynsetDOMTree : function(synset){
		// console.log('building synset tree for ',synset);
		let _li = this.getTag('li');
		let _name = this.getTag('span',[['data-synset-name',synset.name]],synset.name);
		
		let _definition = this.getTag('span',null,synset.definition + ' ('+ synset.part_of_speech + ')');
		_li.appendChild(_name);
		_li.appendChild(_definition);
		_name.addEventListener('click',function(){
			// console.log(this.getAttribute('data-synset-name'));
			document.location.href='/synsets?synset_name=' + this.getAttribute('data-synset-name');
		})
		
		// console.log(synset.examples)
		if(synset.examples.length){
			//_li.appendChild(this.getTag('li'null,'Example:' + synset.examples));
			_li.appendChild(this.getSynsetExampleDOM(synset.examples[0]));
		}
		
		 //console.log(engine.getSynsetList(synset,'lemmas'))
		if(engine.getSynsetList(synset,'lemmas'))    _li.appendChild(this.getSynsetList(synset,'lemmas'));
		if(engine.getSynsetList(synset,'hypernyms')) _li.appendChild(this.getSynsetList(synset,'hypernyms'));
		if(engine.getSynsetList(synset,'hyponyms'))  _li.appendChild(this.getSynsetList(synset,'hyponyms'));
		if(engine.getSynsetList(synset,'meronyms'))  _li.appendChild(this.getSynsetList(synset,'meronyms'));
		if(engine.getSynsetList(synset,'holonyms'))  _li.appendChild(this.getSynsetList(synset,'holonyms'));
		// console.log('synset data:',_li);
		return(_li);
	},
	
	/** build a DOM structure to show an example, if found */
	getSynsetExampleDOM : function(example){
		let _ul = this.getTag('ul');
		let _li = this.getTag('li',[['class','synset_example']],example);
		let _prefix = this.getTag('span',[],'Example: ');
		_li.prepend(_prefix);
		_ul.appendChild(_li);
		return(_ul);
	},
	
	lemmaClickHandler : function(){
		// console.log(this); 
		document.location.href = '/synsets?word=' + this.getAttribute('data-lemma-name');
	},
	
	/** retrieve summaries of all synsets for given pair of words. returns two checkbox lists with unique IDs
	 * for rendering in the comparison columns
	 */
	getSynsetsComparisonLists : function(){
		
		let word1 = document.getElementById('word1').value.replace(/ /g,'_');
		let word2 = document.getElementById('word2').value.replace(/ /g,'_');
		let comparison_type = document.getElementById('comparison_type').value;
		
		// console.log(word1,word2,comparison_type);
		
		/** we need to ensure the URL reflects what is in the box: */
		window.history.replaceState(null,'gish','/synset_similarity?word1=' + word1 + '&word2=' + word2 + '&comparison_type=' + comparison_type);
		proceed = false;
		if(word1 && word2){
			proceed = true;
		}
		
		//synsets_pair_summary
		document.querySelector('#get_synsets_spinner > img').classList.remove('hidden');
		let endpoint = '/api/synsets_pair_summary?word1=' + word1 + '&word2=' + word2;
		
		/** using fetch() api: https://developer.mozilla.org/en-US/docs/Web/API/Fetch_API/Using_Fetch */
		if(proceed){
			
			fetch(endpoint).then((response) => response.json()).then(function(data){
				console.log(data);
				/** update titles: */
				let lhcolTitle = document.querySelector('#word1_results > h3 > span');
				let rhcolTitle = document.querySelector('#word2_results > h3 > span');
	
				let word1_results = document.querySelector('#word1_results > div');
				let word2_results = document.querySelector('#word2_results > div');
				
				/** lookup keys for data output. This includes a JSON node key and a DOM element, set above */
				let syn_key = [{key:'synset1', title:lhcolTitle, target:word1_results},{key:'synset2', title:rhcolTitle, target:word2_results}];			
				
				if(data.status === 'ok'){
					
					/** title - the source words */
					for(let t=0;t<syn_key.length;t++){
						syn_key[t].title.innerText = '';
						syn_key[t].title.appendChild(document.createTextNode(data[syn_key[t].key].source_word));
					}
					
					/** synset data */
					for(let x=0;x<syn_key.length;x++){
						let _ul = engine.getTag('ul');
						let index = 0;
						for(synset of data[syn_key[x].key].synsets){
							
							/** stringify the lemmas array so we can wrap it: */
							let lemmas_string = synset.lemmas.toString().split(',').join(', ');
							let _li = engine.getTag('li');
							let chk = engine.getTag('input',[['type','checkbox'],['name',synset.name],['id',synset.name],['value',synset.name],['data-group',syn_key[x].key], ['data-index',index],['data-pos',synset.part_of_speech]]);
							let lemmas = engine.getTag('span',[],lemmas_string);
							let definition = engine.getTag('span',[],synset.definition)
							let pos = engine.getTag('span',[],'('+synset.part_of_speech+')');
							
							_li.appendChild(chk);
							_li.appendChild(lemmas);
							_li.appendChild(pos);
							_li.appendChild(definition);
							_ul.appendChild(_li);
						}
						index++;
						/** first index is LEFT HAND, second index is RIGHT HAND */
						syn_key[x].target.innerText = '';
						syn_key[x].target.appendChild(_ul);
					}
					document.querySelector('#get_synsets_spinner > img').classList.add('hidden');
				}
				else{
					for(let t=0;t<syn_key.length;t++){
						syn_key[t].title.innerText = '';
						syn_key[t].target.innerText = '';
						// console.log(syn_key[t].target);
						if(t===0) syn_key[t].target.appendChild(document.createTextNode(data.message));
					}
					document.querySelector('#get_synsets_spinner > img').classList.add('hidden');
				}
			});
		}
		else{
			console.log('missing words!');
		}
	},
	
	compareSelectedSynsets : function(){
		/** URL state replace - we need the values form the first part of the page: */
		let word1 = document.getElementById('word1').value.replace(/ /g,'_');
		let word2 = document.getElementById('word2').value.replace(/ /g,'_');
		let comparison_type = document.getElementById('comparison_type').value;

		/** and the selected checkboxes */
		/** we need to ensure the URL reflects what is in the box: */
		
		
		/** TODO!! Need to compare equivalent parts of speech! - i.e. need to add 'verb', 'noun  etc. to the synset info.*/
		
		/** we need two only */
		let checkboxes = document.querySelectorAll('input[type=checkbox]');
		let counter = 0;
		let synsets = [];
		for(checkbox of checkboxes){
			if(checkbox.checked){
				synsets.push(checkbox.value)
				counter++;
			}
		}
		
		window.history.replaceState(null,'gish','/synset_similarity?word1=' + word1 + '&word2=' + word2 + '&comparison_type=' + comparison_type+'&synset1=' + synsets[0]+'&synset2=' + synsets[1]);
		
		proceed = false;
		if(word1 && word2 && counter === 2){
			proceed = true;
		}
		if(proceed){
			document.querySelector('#synset_compare_spinner > img').classList.remove('hidden');
			let endpoint = '/api/synset_similarity_by_name?synset1=' + synsets[0] + '&synset2=' + synsets[1] + '&comparison_type=' + comparison_type;
			fetch(endpoint).then((response) => response.json()).then(function(data){
				console.log('synset compare', data);
				let target = document.getElementById('comparison');
				target.innerText="";
				// target.appendChild(document.createTextNode('Similarity: ' + data.similarity));
				target.appendChild(engine.getSimilarityDOM(data,false));
				document.querySelector('#synset_compare_spinner > img').classList.add('hidden');
			});
		}
		else{
			console.log('Cannot compare synsets! (selected synset count=',counter,', should be 2 only - a bit like the holy hand-grenade, but a bit less)');
			let target = document.getElementById('comparison');
			target.innerText="";
			target.appendChild(engine.getSimilarityDOM({status:'error',message:'Cannot compare synsets! (selected synset count='+counter+', should be 2 only - a bit like the holy hand-grenade, but a bit less)'},true));
			document.querySelector('#synset_compare_spinner > img').classList.add('hidden');
		}
	},

	
	/** 
	 * utilities 
	 * */
	
	
	/**
	 * synset
	 * relationship (lemma, hypernym etc.)
	 * build (bool indicating whether the data should be processed, or just a bool returned as to whether this type exists in the data)
	 * parentElement (the element to attach the name textElement to)
	 */
	getSynsetList : function(synset,relationship){	//synset might be a simple array of lemmas... arg 3=boo
		//console.log(synset);
		if(synset[relationship].length){
			let _ul = engine.getTag('ul');
			//let _li_name = engine.getTag('li',null,relationship); //continue from here
			//let _li_name = engine.getTag('li');
			let _li_list = engine.getTag('li',null,relationship);
			
			/** TODO I need to append the outot to the FIRST li*/
			
			let _ul_list_wrapper = engine.getTag('ul');
			
			for(synonym of synset[relationship]){
				if (relationship === "lemmas"){
					display_name = synonym;	//a bit hacky - this is just an array of lemma strings
				}
				else{
					display_name = synonym.name;
				}
				let _li_list_item = engine.getTag('li',null,display_name);
				
				if(relationship === 'lemmas'){
					_li_list_item.setAttribute('data-lemma-name',display_name);
					_li_list_item.setAttribute('class','lemma');
					_li_list_item.setAttribute('title','click to reload with this lemma as word');
					_li_list_item.addEventListener('click',engine.lemmaClickHandler);
				}
				// console.log(relationship);
				if(['hypernyms','hyponyms','meronyms','holonyms'].includes(relationship)){
					_li_list_item.setAttribute('data-synset-name',synonym.name);
					// console.log('append synset load by name handler');
					_li_list_item.setAttribute('class','synset');
					_li_list_item.setAttribute('title','click for details of this synset');
					_li_list_item.addEventListener('click',function(){
						// console.log(this.getAttribute('data-synset-name'));
						document.location.href='/synsets?synset_name=' + this.getAttribute('data-synset-name');
					})
				}
				
				_ul_list_wrapper.appendChild(_li_list_item);
			}
			
			//_li_list.appendChild();
			_li_list.appendChild(_ul_list_wrapper);
			//_ul.appendChild(_li_name);
			_ul.appendChild(_li_list);
			// console.log('child synset list:',_ul);
			return(_ul);
		}
		else{
			return(false);
		}
	},
	
	/** process the two text boxes on the /phrase_compare page, checking for the state of the checkboxes as well */
	preProcessPhrases : function(){
		console.log('pre-procesing phrases')
		let p1 = document.getElementById('p1').value
		let p2 = document.getElementById('p2').value;
		// console.log(p1, p2);
		// console.log(p1.split(/ /g));
		
		let remove_stopwords = true;
		if(document.getElementById('remove_stopwords').checked){
			remove_stopwords = false;
		}
		let perform_stem = true; 
		if(!document.getElementById('perform_stem').checked){
			perform_stem = false;
		}
		let stemmer = document.getElementById('selected_stemmer').value;
			
		lists = [[p1.split(/ /g)],[p2.split(/ /g)]];
		// console.log(lists);
		let format = 'complex';
		for(let x=1;x<=lists.length;x++){
			let endpoint = '/api/get_processed_list?words=' + ( eval('p'+x).split(/ /g));
			if(!remove_stopwords){
				endpoint += '&remove_stopwords=false';
			}
			if(!perform_stem){
				endpoint += '&perform_stem=false';
				format = 'simple';	//a legacy of API dev...seemed silly to use the same format as stemmed output, because redundant data...
			}
			if(perform_stem){
				endpoint += '&stemmer=' + stemmer;
			}
			// console.log(endpoint);
			fetch(endpoint).then((response) => response.json()).then(function(data){
				// console.log(data);
				let new_phrase = new Array();
				for(let y=0;y<data.processed_list.length;y++){
					if(data.perform_stem){
						if(format === 'complex'){
							new_phrase.push(data.processed_list[y].stemmed_word);
						}
						else{
							//see comment above
							new_phrase.push(data.processed_list[y]);
						}
					}
					else{
						/** re-use input words, except for removed stopwords (maybe should make teh return structure the same?) */
						new_phrase.push(data.processed_list[y]);
					}
				}
				/** and append to field */
				document.getElementById('p'+x+'_processed').innerHTML = "";
				document.getElementById('p'+x+'_processed').appendChild(document.createTextNode(new_phrase.join(' ')));
			});
		}
	},
	
	comparePhrases : function(){
		console.log('compare phrases');
		/** 
		 * obtain the values from the preview and the comparison type radio buttons 
		 * Pass these to the back-end and there, a pairwise word comparison will be done, 
		 * returning the highest score for any individual word comparison. It's crude...
		*/
		document.querySelector('#phrase_compare_spinner > img').classList.remove('hidden');
		let p1 = document.getElementById('p1_processed').innerText;
		let p2 = document.getElementById('p2_processed').innerText;
		let comp_type = document.querySelector('input[name="comparison_type"]:checked').value;
		/** TODO: The back-end will eventually accept additional arguments of 'phrase_ct=xxx' (currently defaulting to 'pairwise')
        and 'word_ct=xxx (only relevant for crude comparison by words, defaulting to 'wup' as elsewhere) */
		let endpoint = '/api/phrase_similarity?p1=' +p1+ '&p2=' + p2 + '&phrase_ct=' + comp_type;
		fetch(endpoint).then((response) => response.json()).then(function(data){
			console.log(data);	
			let wrapper = document.getElementById('output');
			wrapper.innerText = "";
			if(data.status==='ok'){
				
				if(data.phrase_comparison_type === 'pw'){ //pair-wise
					engine.getPairwiseResult(data,wrapper);
				}
				if(data.phrase_comparison_type === 'cos'){ //cosine
					engine.getCosineResult(data,wrapper);
				}
				
				if(data.phrase_comparison_type === 'tf'){ //tensorflow
					engine.getCosineResult(data,wrapper);
				}
				
				if(data.phrase_comparison_type === 'rb'){ //roberta
					engine.getCosineResult(data,wrapper);
				}
				
				
				
//				let title = engine.getTag('h2',false, 'Best match')	//TODO: thois will need to adapt if other methods are used
//				wrapper.appendChild(title);
//				
//				let p1_processed = engine.getTag('div')
//				let p2_processed = engine.getTag('div')
//				
//				//SCORE
//				let score_wrapper = engine.getTag('div',false,'Similarity score:');
//				let score = engine.getTag('span',false,data['result']['calculated_similarity']);
//				score_wrapper.appendChild(score);
//				
//				//WORDS:
//				let p1_word_wrapper = engine.getTag('div',false,'Word 1:')
//				let p2_word_wrapper = engine.getTag('div',false,'Word 2:')
//				
//				let w1 = data['result']['synsets'][0]['root_word'];
//				let p1_word = engine.getTag('span',
//				[
//					['data-word', w1 ],
//					['title','click to see all '+w1+' synsets']  
//				
//				],
//				data['result']['synsets'][0]['root_word']);
//				
//				
//				p1_word.addEventListener('click', function(){document.location="/synsets?word="+this.getAttribute('data-word')});
//				p1_word_wrapper.appendChild(p1_word)
//				
//				let w2 = data['result']['synsets'][1]['root_word']
//				let p2_word = engine.getTag('span',[
//					[ 'data-word', w2 ],
//					['title','click to see all '+w2+' synsets'] 
//				],
//				data['result']['synsets'][1]['root_word']);
//				p2_word.addEventListener('click', function(){document.location="/synsets?word="+this.getAttribute('data-word')});
//				p2_word_wrapper.appendChild(p2_word)
//				
//				p1_processed.appendChild(p1_word_wrapper);
//				p2_processed.appendChild(p2_word_wrapper);
//	
//				
//				//SYNSETS:
//				let p1_synset_wrapper = engine.getTag('div',false,'Matching synset 1:');
//				let p2_synset_wrapper = engine.getTag('div',false,'Matching synset 2:');
//				
//				let p1_synset = engine.getTag('span',[['data-synset-name',data['result']['synsets'][0]['synset']['name']],['title','Click to see synset details']],data['result']['synsets'][0]['synset']['name']);
//				p1_synset.addEventListener('click', function(){document.location="/synsets?synset_name="+this.getAttribute('data-synset-name')});
//				// p1_synset.addEventListener('click', res => document.location="/synsets?synset_name="+this.getAttribute('data-synset-name'));	//can't use this because 'this' is not defined
//				
//				p1_synset_wrapper.appendChild(p1_synset)
//				
//				let p2_synset = engine.getTag('span',[['data-synset-name', data['result']['synsets'][1]['synset']['name']],['title','Click to see synset details']],      data['result']['synsets'][1]['synset']['name']);
//				p2_synset.addEventListener('click', function(){document.location="/synsets?synset_name="+this.getAttribute('data-synset-name')})
//				p2_synset_wrapper.appendChild(p2_synset);
//				
//				
//				
//				let p1_synset_definition = engine.getTag('span',false,data['result']['synsets'][0]['synset']['definition']);
//				p1_synset_wrapper.appendChild(p1_synset_definition);
//				let p2_synset_definition = engine.getTag('span',false,data['result']['synsets'][1]['synset']['definition']);
//				p2_synset_wrapper.appendChild(p2_synset_definition);
//				p1_processed.appendChild(p1_synset_wrapper);
//				p2_processed.appendChild(p2_synset_wrapper);
//				
//				
//				// push result to output element	
//				wrapper.appendChild(score_wrapper);		
//				wrapper.appendChild(p1_processed);
//				wrapper.appendChild(p2_processed);
			}
			else{
				//an error
				let title = engine.getTag('h2',false, 'Error')
				wrapper.appendChild(title);
				
				// TODO: this could output better messaging
				let err = engine.getTag('div',false,data['message']);
				wrapper.appendChild(err);
			}
			
			document.querySelector('#phrase_compare_spinner > img').classList.add('hidden');
		});
	},
	
	getCosineResult : function(data, wrapper){
		console.log('in cosineresult renderer',data);
		//let title = engine.getTag('h2',false, 'Cosine similarity');
		let title = engine.getTag('h2',false, data.result.method);
		wrapper.appendChild(title);
		
		let p1_processed = engine.getTag('div')
		let p2_processed = engine.getTag('div');
		
						//SCORE
		let score_wrapper = engine.getTag('div',false,'Similarity score:');
		let score = engine.getTag('span',false,data['result']['calculated_similarity']);
		score_wrapper.appendChild(score);
		
						// push result to output element	
		wrapper.appendChild(score_wrapper);		
		wrapper.appendChild(p1_processed);
		wrapper.appendChild(p2_processed);
		
	},
	
	getPairwiseResult : function(data, wrapper){
		console.log('in pairwiseresult renderer')
				let title = engine.getTag('h2',false, 'Highest word similarity')	//TODO: thois will need to adapt if other methods are used
				wrapper.appendChild(title);
				
				let p1_processed = engine.getTag('div')
				let p2_processed = engine.getTag('div')
				
				//SCORE
				let score_wrapper = engine.getTag('div',false,'Similarity score:');
				let score = engine.getTag('span',false,data['result']['calculated_similarity']);
				score_wrapper.appendChild(score);
				
				//WORDS:
				let p1_word_wrapper = engine.getTag('div',false,'Word 1:')
				let p2_word_wrapper = engine.getTag('div',false,'Word 2:')
				
				let w1 = data['result']['synsets'][0]['root_word'];
				let p1_word = engine.getTag('span',
				[
					['data-word', w1 ],
					['title','click to see all '+w1+' synsets']  
				
				],
				data['result']['synsets'][0]['root_word']);
				
				
				p1_word.addEventListener('click', function(){document.location="/synsets?word="+this.getAttribute('data-word')});
				p1_word_wrapper.appendChild(p1_word)
				
				let w2 = data['result']['synsets'][1]['root_word']
				let p2_word = engine.getTag('span',[
					[ 'data-word', w2 ],
					['title','click to see all '+w2+' synsets'] 
				],
				data['result']['synsets'][1]['root_word']);
				p2_word.addEventListener('click', function(){document.location="/synsets?word="+this.getAttribute('data-word')});
				p2_word_wrapper.appendChild(p2_word)
				
				p1_processed.appendChild(p1_word_wrapper);
				p2_processed.appendChild(p2_word_wrapper);
	
				
				//SYNSETS:
				let p1_synset_wrapper = engine.getTag('div',false,'Matching synset 1:');
				let p2_synset_wrapper = engine.getTag('div',false,'Matching synset 2:');
				
				let p1_synset = engine.getTag('span',[['data-synset-name',data['result']['synsets'][0]['synset']['name']],['title','Click to see synset details']],data['result']['synsets'][0]['synset']['name']);
				p1_synset.addEventListener('click', function(){document.location="/synsets?synset_name="+this.getAttribute('data-synset-name')});
				// p1_synset.addEventListener('click', res => document.location="/synsets?synset_name="+this.getAttribute('data-synset-name'));	//can't use this because 'this' is not defined
				
				p1_synset_wrapper.appendChild(p1_synset)
				
				let p2_synset = engine.getTag('span',[['data-synset-name', data['result']['synsets'][1]['synset']['name']],['title','Click to see synset details']],      data['result']['synsets'][1]['synset']['name']);
				p2_synset.addEventListener('click', function(){document.location="/synsets?synset_name="+this.getAttribute('data-synset-name')})
				p2_synset_wrapper.appendChild(p2_synset);
				
				
				
				let p1_synset_definition = engine.getTag('span',false,data['result']['synsets'][0]['synset']['definition']);
				p1_synset_wrapper.appendChild(p1_synset_definition);
				let p2_synset_definition = engine.getTag('span',false,data['result']['synsets'][1]['synset']['definition']);
				p2_synset_wrapper.appendChild(p2_synset_definition);
				p1_processed.appendChild(p1_synset_wrapper);
				p2_processed.appendChild(p2_synset_wrapper);
				
				
				// push result to output element	
				wrapper.appendChild(score_wrapper);		
				wrapper.appendChild(p1_processed);
				wrapper.appendChild(p2_processed);
		
	},
	
	loadSynsetUIPage : function(synsetName){
		target = "/synsets";
		if(synsetName){
			target += '?synset_name=' + synsetName;
		}
		document.location = target;
	},
	
	/** TODO: */
	selectStemmerType : function(){
		console.log(this.value);
	},
	
	toggleStemmerVisibility : function(){
		// console.log(this.checked);/** Nice! the 'this' context is transferred as expected to the handler */
		if(this.checked){
			document.getElementById('stemmer_types').classList.remove('hide_stemmer_types');
		}
		else{
			document.getElementById('stemmer_types').classList.add('hide_stemmer_types');
		}
		document.getElementById('destop').click();
	},
	
	stemmerTypesHandler : function(){
		// console.log(this.value, this.checked);
		document.getElementById('selected_stemmer').value = this.value;
		document.getElementById('destop').click();
	},
	
	stopwordsCheckboxHandler: function(){
		document.getElementById('destop').click();
	}, 
	
	handlePhraseBlur : function(){
		document.getElementById('destop').click();
	},
	
	
	
	relatedPhraseJobClickHandler : function(){
		/** TODO: This will eventually be a handler to indicat4e WHICH job the UI is currently working on */
		console.log(this.getAttribute('data-comparison-type'));
		document.getElementById('selected_job_comparison_type').value = this.getAttribute('data-comparison-type');
	},
	
	
	handleThresholdKeyUp : function(){
		/** ensure a float, and precedng zero if first char is '.' */
//		let elem = document.getElementById('comparison_threshold');
/*		if(
			(parseInt(elem.value[elem.value.length-1] === false) )){
			elem.value = elem.value.slice(0,-1); 
		}*/
//		if (elem.value[0] === '.'){
//			elem.value = '0' + elem.value;
//		}
//		if(elem.value.length > 2 && isNaN(parseInt(elem.value.charAt(elem.value.length - 1)))){
//			elem.value = elem.value.slice(0,-1);
//			console.log(elem.value.slice(0,-1));
//		}
//		if(elem.value.length > 1){	//to account for the - sign potentially
//			elem.value = parseFloat(elem.value)
//		}
	},
		
	getFilteredTerms : function(){
		let filter = document.getElementById('term').value;
		this.relatedTermsLookupData = false;
		if(filter.length === 2){
			engine.getTemporaryAutocompletePhraseData();
		}
		if(filter.length > 2){
			/** use the above data */
			console.log(engine.temporaryAutocompletePhraseData['filtered']);
			$(function(){
				console.log('starting autocomplete render');
				$('#term').autocomplete({
					'source' : engine.temporaryAutocompletePhraseData['filtered']
				})
				console.log('end autocomplete render');
			})
		}
//		if(filter.length > 1){
//			console.log(filter);
//			/** gonna need jquery here. Also, the blur of the threshold will run an ajax query to get teh data up front.. */
//			let job_uuid = document.querySelector('input[name="job_uuid"]:checked').value;
//			let limit = document.getElementById('comparison_threshold').value;
//			let endpoint = '/api/get_filtered_terms?job_uuid='+job_uuid+'&term='+filter + '&limit=' + limit;
//			fetch(endpoint)
//				.then( response => response.json() ) //This doesn't like being multi-line. Don't know why...
//				.then(function(data){
//					console.log(data);
//				/** build an array for jquery to act on */
//				let test = $('#comparison_threshold');
//				console.log(test);
//				$(function(){
//					console.log('starting autocomplete render');
//					$('#term').autocomplete({
//						'source':data['filtered']
//					})
//					console.log('end autocomplete render');
//				})
//			})
//		}
	},
	
	getTemporaryAutocompletePhraseData : function(){
		let filter = document.getElementById('term').value;
		document.getElementById('term').setAttribute('disabled','disabled');
		/**
		 * we just want to front-load teh data so we can do faster suggestions. The DOM stuff ermains on the 'term' keyup handler
		 * This function also disables/enables the field as it is doing the lookup:
		 **/		
		let job_uuid = document.querySelector('input[name="job_uuid"]:checked').value;
		let limit = document.getElementById('comparison_threshold').value;
		let endpoint = '/api/get_filtered_terms?job_uuid='+job_uuid+'&term='+filter + '&limit=' + limit;
		
		fetch(endpoint)
			.then( response => response.json() ) //This doesn't like being multi-line. Don't know why...
			.then(function(data){
				engine.temporaryAutocompletePhraseData = data
				console.log(data);
/*			$(function(){
				console.log('starting autocomplete render');
				$('#term').autocomplete({
					'source':data['filtered']
				})
				console.log('end autocomplete render');
			})*/
			document.getElementById('term').removeAttribute('disabled');
			document.getElementById('term').focus();
		})

	},
	
	getSimilarityDOM : function(data,isError){
		// console.log(data);
		let wrapper = this.getTag('div');
		let h4 = this.getTag('h4')
		let text = ''
		if(isError){
			h4.appendChild(document.createTextNode(data.status));
			text = document.createTextNode(data.message)    
			//wrapper.appendChild(document.createTextNode(data.message));
		}
		else{
			
			h4.appendChild(document.createTextNode(data.comparison_type + ' comparison'));
			/** we may also get an error back from the comprison itself: */
			if(data.similarity.status === 'ok'){
				
				text = document.createTextNode(data.similarity.comparison)
			}
			else{
				h4.innerText = '';
				h4.appendChild(document.createTextNode(data.similarity.status));
				text = document.createTextNode(data.similarity.message);
			}
		}
		wrapper.appendChild(h4);
		wrapper.appendChild(text);
		return(wrapper)
	},
	
	getTag : function(tagname,attrs,text){
		if(! text){
			text = " ";
		}
		let _tag = document.createElement(tagname);
		if(attrs){	//attrs is a nested array
			/** add attributes to tag */
			for(let a=0;a<attrs.length;a++){
				_tag.setAttribute(attrs[a][0],attrs[a][1]);
			}
		}
		if(text){
			/** append a text node */
			_tag.appendChild(document.createTextNode(text));
		}
		return(_tag);
	},
	
	_getQSVal : function(url,param){
		var _params = decodeURI(url).split('?');
		var _out = '';
		if(_params.length === 2){
			var _bits = _params[1].split(/&/g);
			for(var b=0;b<_bits.length;b++){
				if(_bits[b].split(/=/)[0] === param){
					//get rid of hash, if found:
					_out = _bits[b].split(/=/)[1];
					if(_out.indexOf('#') !== -1){
						_out = _out.split(/#/)[0];
					}
					return(_out);
				}
			}
		}
		return(null);
	},
}

document.addEventListener('load',engine.init());
