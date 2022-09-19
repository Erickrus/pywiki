function Api() {
  this.history = new Array();

  this.wikiModify = function() {
     console.log("api.wikiModify()");
     var mdUrl = document.getElementById('mdUrl').value;
     var mdText = document.getElementById('mdEdit').value;
     $.post(
      '/wiki/api/modify',
      {
        "json": JSON.stringify({"mdUrl": mdUrl, "mdText":mdText })
      },

      function(returnedData) {
        console.log("api.wikiModify.response()");
        console.log(returnedData)

        var $el = $('#md');
        $el.empty();
        $el.append(returnedData['data']['content']);
        MathJax.Hub.Queue(['Typeset', MathJax.Hub, $el[0]]);

        //document.getElementById('mdEdit').value = returnedData['data']['md'];

        document.getElementById("viewTab").click();
      },
      'json'
    );
  };
  this.wikiPage = function(historyCall) {
    console.log("api.wikiPage()");
    var mdUrl = document.getElementById('mdUrl').value;
    if (!historyCall) {
      this.history.push(mdUrl);
    }
    $.post(
      '/wiki/api/page',
      {
        "json": JSON.stringify({"mdUrl": mdUrl })
      },
      function(returnedData) {
        console.log("api.wikiPage.response()");
        console.log(returnedData)
        //document.getElementById('md').innerHTML = returnedData['data']['content']

        var $el = $('#md');
        $el.empty();
        $el.append(returnedData['data']['content']);
        MathJax.Hub.Queue(['Typeset', MathJax.Hub, $el[0]]);

        document.getElementById('mdEdit').value = returnedData['data']['md'];

        document.getElementById("viewTab").click();
      },
      'json'
    );
  };
  this.backward = function() {
    if (this.history.length >1) {
       this.history.pop();
       var mdUrl = this.history[this.history.length-1];
       console.log(mdUrl);
       if (mdUrl.toLowerCase().endsWith('.html')) {
          mdUrl = mdUrl.substring(0, mdUrl.length-5) + ".md";
          
       }
       document.getElementById('mdUrl').value = mdUrl;
       this.wikiPage(true);
    }
    

  }
  this.goto = function(mdUrl) {
      if (mdUrl.toLowerCase().endsWith('.html')) {
          mdUrl = mdUrl.substring(0, mdUrl.length-5) + ".md";
          
      }
      document.getElementById('mdUrl').value = mdUrl;
      this.wikiPage(false);
  };
}

var api = new Api();
