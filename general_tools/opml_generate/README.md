OPML Generator
==============

*This tool generates a valid OPML file that contains the RSS feed for every change in every configured 
language in Door43.*

**FIXME**: this tool needs to be created.


Notes:

* The list of language codes exists in a PHP array in a file called "local.php", which is updated when 
  new languages are added to Door43:

```
$conf['plugin']['translation']['translations'] = 'ab abp ae af ak am an ar as av ay az ba be bg bh bi blx bm bn bnp bo br bs ca ce ch cnh co cr cs cu cv cy da de dv dz ee el en eo es et eu fa ff fi fj fo fr fy ga gd gl gn gu gv ha he hi ho hr ht hu hy hz ia id ie ig ii ik ilo io is it iu ja jv ka kg ki kj kk kl km kn ko kr ks ku kv kw ky la lb lg li ln lo lt lv mg mh mi mk ml mn mr ms mt my na nb nd ne ng nl nn no nr nv ny oc oj om or os pa pi pl ps pt pt-br qu rm rn ro ru rw sa sc sd se sg shn si sk sl sm sn so sq sr ss st su sv sw ta te tg th ti tk tl tn to tr ts tt tw ty ug uk ur uz ve vi vo wa wo xh xmf yi yo za zh zh-tw zu';
```

* The language names in their vernacular (self-names) with indigenous spellings are in a file called 
  "languages.txt", which is updated when new languages are added to Door43:

```
aa	Afaraf
ab	Аҧсуа
abp	Ayta Abellen
ae	Avesta
af	Afrikaans
ak	Akan
am	አማርኛ
```


