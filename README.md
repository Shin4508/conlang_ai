# Conlang_ai
try here 
https://shin4508.github.io/recipe_encoder/
## what it is
conlang means the language created by a person or groups(ex: Nave from Avatar, Dothraki from Game of Thrones)
conlang has many steps to accomplish, but I focused on Pronunciation for now
## how it works
The model is based on char-level transformer. List words include '\n' to ouput word list.
Word list from 5 language -> IPA word list -> model -> IPA word list
Put IPA(International Phonetic Alphabet) into Tokenizer and prepare the text data from 3~5 different languages.
This model doesn't have to seek accuracy because there is no correct answer to this generation, so bias and variance is accuracy.
but the output sounds like new language.
### To generate word from ipa evenly
let the model predict 10 words and search the ipa that used the least and put it into prompt and generate another 10 words and keep looping

