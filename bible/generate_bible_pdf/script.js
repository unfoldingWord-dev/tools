if (!String.prototype.startsWith) {
    String.prototype.startsWith = function(searchString, position) {
        position = position || 0;
        return this.indexOf(searchString, position) === position;
    };
}

if (!String.prototype.includes) {
    Object.defineProperty(String.prototype, 'includes', {
        value: function(search, start) {
          if (typeof start !== 'number') {
               start = 0
          }
          if (start + search.length > this.length) {
               return false
          } else {
              return this.indexOf(search, start) !== -1
          }
        }
    })
}

function addMatchingFootnotes(str, footnotesSection, footnotes) {
    var itemFootnotes = [];
    if (! str.includes('ref-fn-')) {
        return itemFootnotes
    }
    if (! footnotesSection.contents().length) {
        itemFootnotes.push($('<hr class="footnotes-hr"/>'));
    }
    var re = /ref-(fn-\d+-\d+-\d+-\d+)/g;
    while (match = re.exec(str)) {
        var idx = match[1];
        if (footnotes[idx]) {
            itemFootnotes.push($(footnotes[idx]));
        }
    }
    itemFootnotes.forEach(function(element) {
        element.appendTo(footnotesSection);
    });
    return itemFootnotes;
}

function removeMatchingFootnotes(itemFootnotes) {
    if (itemFootnotes.length) {
        itemFootnotes.forEach(function(element) {
            element.detach();
        });
    }
 }

$(document).ready(function(){
    var books = $('.bible-book-text');
    books.each(function(bookIdx) {
        var book = books[bookIdx];
        var contents = $(book).contents();
        $(book).empty();
        console.log(contents);

        var footnotes = {}
        contents.each(function(contentIdx) {
            var content = this;
            if (content.localName === 'div' && content.className === 'footnotes') {
                for (var i = 0; i < content.childNodes.length; ++i) {
                    childNode = content.childNodes[i];
                    if (childNode.id.startsWith('fn-')) {
                        footnotes[childNode.id] = childNode;
                    }
                }
            }
        });
        console.log(footnotes);
        
        var pageIdx = 0;
        var colIdx = 0;

        var page = $('<div id="page-'+pageIdx+'" class="page"></div>');
        page.appendTo(book);
        var col1 = $('<div id="col-'+colIdx+'" class="col left"></div>');
        col1.appendTo(page);
        var col2 = $('<div id="col-'+(colIdx+1)+'" class="col right"></div>');
        col2.appendTo(page);

        var footnotesSection1 = $('<div id="fns-'+colIdx+'" class="footnotesSection left footnotes"></div>');
        footnotesSection1.appendTo(page);
        var footnotesSection2 = $('<div id="fns-'+(colIdx+1)+'" class="footnotesSection right footnotes"></div>');
        footnotesSection2.appendTo(page);

        var col = page.find('#col-'+colIdx);
        var footnotesSection = page.find('#fns-'+colIdx);

        contents.each(function(contentIdx) {
            var content = this;
            var $content = $(this);
            if (content.localName == 'p' || content.localName == 'h1' || content.localName == 'h2') {
                console.log('Outer: '+content.outerHTML.replace('\n', ' ').slice(0,40)+'...');
                $content.appendTo(col);
                var itemFootnotes = addMatchingFootnotes($content.html(), footnotesSection, footnotes);
                var colHeight = col.height() + footnotesSection.height() + ($content.prop("tagName")==='H2'?100:0); // last part makes h2 not be on last line
                var pageHeight = page.height();
                if (colHeight > pageHeight) {
                    $content.detach();
                    removeMatchingFootnotes(itemFootnotes);                
                    var items = [];
                    var lastItemWasVerseNum = false;
                    for (var i = 0; i < content.childNodes.length; i++) {
                        var childNode = content.childNodes[i];
                        if (childNode.nodeType === 3) {
                            if (childNode.nodeValue.trim().length) {
                                var words = childNode.nodeValue.trim().split(/ +/g).map(function(val){return val+' '});
                                if (lastItemWasVerseNum) {
                                    items[items.length-1] = items[items.length-1]+words.shift();
                                    lastItemWasVerseNum = false;
                                }
                                items = items.concat(words);
                            }
                        } 
                        else if(childNode.nodeType === 1) {
                            if (childNode.className == 'v-num') {
                                lastItemWasVerseNum = true;
                                items.push(childNode.outerHTML);
                            }
                            else if(childNode.id.startsWith('ref-fn-')) {
                                items[items.length-1] = items[items.length-1].trim()+childNode.outerHTML+' ';
                            }
                            else if(content.localName === 'div' && content.className === 'footnotes') {
                                // do nothing, already have footnotes
                            }
                            else if(content.localName === 'div') {
                                items.push(childNode.outerHTML+' ');
                            }
                            else if (childNode.className == 'chunk-break') {
                                // do nothing
                            }
                            else {
                                console.log('=========> UNKNOWN CHILDNODE: '+childNode.outerHTML);
                            }
                        }
                        else {
                            console.log("================> UNKONWN CHILDNODE TYPE: "+childNode.nodeType+" -> "+childNode.outerHTML);
                        }
                    }
                    wrapper = $content.clone().empty();
                    wrapper.appendTo(col);
                    while(items.length) {
                        var item = items.shift();
                        // console.log("Item is: "+item);
                        var wrappedItem = $('<span>'+item+'</span>');
                        wrappedItem.appendTo(wrapper);
                        itemFootnotes = addMatchingFootnotes(item, footnotesSection, footnotes);
                        var colHeight = col.height() + footnotesSection.height() + ($content.prop("tagName")==='H2'?100:0); // last part makes h2 not be on last line;
                        var pageHeight = page.height();
                        if (colHeight > pageHeight) {
                            ++colIdx;
                            wrappedItem.detach();
                            removeMatchingFootnotes(itemFootnotes);
                            if (wrapper.is(':empty')) {
                                wrapper.detach();
                            } else {
                                var oldWrapper = wrapper;
                                wrapper = $content.clone().empty();
                                if (oldWrapper.prop("tagName") === 'P')
                                    oldWrapper.addClass('split-paragraph'); // so we can justify the last line of this split paragraph
                            }
                            if (colIdx % 2 === 0) {
                                ++pageIdx;
                                page = $('<div id="page-'+pageIdx+'" class="page"/>');
                                page.appendTo(book);
                                col1 = $('<div id="col-'+colIdx+'" class="col left"/>');
                                col1.appendTo(page);
                                col2 = $('<div id="col-'+(colIdx+1)+'" class="col right"/>');
                                col2.appendTo(page);
                                footnotesSection1 = $('<div id="fns-'+colIdx+'" class="footnotesSection left footnotes"></div>');
                                footnotesSection1.appendTo(page);
                                footnotesSection2 = $('<div id="fns-'+(colIdx+1)+'" class="footnotesSection right footnotes"></div>');
                                footnotesSection2.appendTo(page);
                            }
                            col = page.find('#col-'+colIdx);
                            footnotesSection = page.find('#fns-'+colIdx);
                            wrapper.appendTo(col);
                            items.unshift(item);
                        }
                        else {
                            wrappedItem.detach();
                            wrapper.html(wrapper.html() + wrappedItem.html());
                        }
                    }
                }
            }
        });
    });
});
