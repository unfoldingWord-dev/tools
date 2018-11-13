if (!String.prototype.startsWith) {
    String.prototype.startsWith = function(searchString, position) {
        position = position || 0;
        return this.indexOf(searchString, position) === position;
    };
}

$(document).ready(function(){
    var area = $('.bible-book-text');
    var contents = area.contents();
    var pageIdx = 0;
    var colIdx = 0;
    var page = $('<div id="page'+pageIdx+'" class="page"></div>');
    page.appendTo(area);
    var col = $('<div id="col'+colIdx+'" class="col"></div>');
    col.appendTo(page);
    console.log(contents.clone());
    console.log(contents);
    contents.each(function(contentIdx) {
        var content = this;
        var $content = $(this);
        console.log('Got content of tag <'+content.localName+' '+content.id+' '+content.className+'>');
        if (content.localName == 'p' || content.localName == 'h2' || content.localName == 'h1' || content.localName == 'div') {
            $content.detach();
            console.log('Is a '+content.localName);
            console.log('trying to append');
            $content.appendTo(col);
            console.log('Trying to put container: '+col.height()+' > '+page.height())
            if(col.height() > page.height()){
                $content.detach();

                var items = [];
                var lastItemWasVerseNum = false;
                for (var i = 0; i < content.childNodes.length; i++) {
                    var childNode = content.childNodes[i];
                    if (childNode.nodeType === 3) {
                        if (childNode.nodeValue.trim().length) {
                            var words = childNode.nodeValue.trim().split(/ +/g).map(function(val){return val+' '});
                            if (lastItemWasVerseNum) {
                                items[items.length-1] = items[items.length-1].trim()+words.shift();
                                lastItemWasVerseNum = false;
                            }
                            items = items.concat(words);
                        }
                    } 
                    else if(childNode.nodeType === 1) {
                        if (childNode.className == 'v-num') {
                            lastItemWasVerseNum = true;
                            items.push(childNode.outerHTML+' ');
                        }
                        else if(childNode.id.startsWith('ref-fn-')) {
                            items[items.length-1] = items[items.length-1].trim()+childNode.outerHTML+' ';
                        }
                        else if(content.localName === 'div') {
                            items.push(childNode.outerHTML+' ');
                        }
                        else if (childNode.className == 'chunk-break') {
                            // do nothing
                        }
                        else {
                            console.log('=========> GOT THIS FUNKY THING: '+childNode.outerHTML);
                        }
                    }
                    else {
                        console.log(childNode.nodeType);
                        console.log("================> Have a node of "+childNode.nodeType+" -> "+childNode.outerHTML);
                    }
                }
    
                wrapper = $content.clone().empty();
                wrapper.appendTo(col);
                while(items.length) {
                    var item = items.shift();
                    console.log("our item is: "+item);
                    var element = $('<span>'+item+'</span>');
                    $(element).appendTo(wrapper);
                    console.log('appended to wrapper, wrapper now has '+wrapper.contents().length+' children');
                    console.log(wrapper.parent().height()+' > '+wrapper.parent().parent().height(), wrapper.parent().height() > wrapper.parent().parent().height());
                    var colHeight = col.height();
                    var pageHeight = page.height();
                    if (colHeight > pageHeight) {
                        ++colIdx;
                        $(element).detach();
                        if (wrapper.is(':empty')) {
                            wrapper.detach();
                        } else {
                            wrapper = $content.clone().empty();
                        }
                        if (colIdx % 2 === 0) {
                            ++pageIdx;
                            page = $('<div id="page'+pageIdx+'" class="page"/>');
                            page.appendTo(area);
                        }
                        col = $('<div id="col'+colIdx+'" class="col"/>');
                        col.appendTo(page);
                        wrapper.appendTo(col);
                        items.unshift(item);
                    }
                    else {
                        $(element).detach();
                        wrapper.append(item);
                        //console.log("all is good for "+colIdx);
                        //console.log(wrapper.html());
                    }
                }
            }
        }
    });
});
