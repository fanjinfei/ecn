(function($) {
  $(document).ready(function() {

    var langCode = $('html').attr('lang');
    var showMore = '';
    var showFewer = '';

    if (langCode == 'fr') {
      var showMore = 'Montrer tout';
      var showFewer = 'Montrer moins';
    } else {
      var showMore = 'Show more';
      var showFewer = 'Show fewer';
    }

    $('#filters ul').each(function() {
      var LiN = $(this).find('li').length;
      if (LiN > 10) {
        $('li', this).eq(9).nextAll().hide().addClass('toggleable');
        $(this).append('<li class="small list-group-item more">' + showMore + '</li>');
      }
    });

    $('#filters ul').on('click', '.more', function() {

      if ($(this).hasClass('less')) {
        $(this).text(showMore).removeClass('less');
      } else {
        $(this).text(showFewer).addClass('less');
      }

      $(this).siblings('li.toggleable').slideToggle();

    });

    $("#fctstartOver").click(function() {
      $("#mainForm").find("#search").val("");
      $("#mainForm").find("#scoreSort").attr("selected","selected");
      $("#mainForm").find("#showSum").val("hide");
      $("input").remove("[name='fq']");
      $("#mainForm").submit();
    });

    $("#startOver").click(function() {
      $("#mainForm").find("#search").val("");
      $("#mainForm").find("#scoreSort").attr("selected","selected");
      $("#mainForm").find("#showSum").val("hide");
      $("input").remove("[name='fq']");
      $("#mainForm").submit();
    });

    if ($('#ra:checked').val() != undefined) {
      var url = $('#fctstartOver').attr('href');
      if (url != undefined) {
        url = url.replace(/stclac%3A2/, 'stclac%3A1');
        $('#fctstartOver').attr('href', url);
      }

      var url = $('#startOver').attr('href');
      if (url != undefined) {
        url = url.replace(/stclac%3A2/, 'stclac%3A1');
        $('#startOver').attr('href', url);
      }
    }

    $('#rc').click(function() {
      var url = $('#fctstartOver').attr('href');
      if (url != undefined) {
        url = url.replace(/stclac%3A1/, 'stclac%3A2');
        $('#fctstartOver').attr('href', url);
      }

      var url = $('#startOver').attr('href');
      if (url != undefined) {
        url = url.replace(/stclac%3A1/, 'stclac%3A2');
        $('#startOver').attr('href', url);
      }
    });

    $('#ra').click(function() {
      var url = $('#fctstartOver').attr('href');
      if (url != undefined) {
        url = url.replace(/stclac%3A2/, 'stclac%3A1');
        $('#fctstartOver').attr('href', url);
      }

      var url = $('#startOver').attr('href');
      if (url != undefined) {
        url = url.replace(/stclac%3A2/, 'stclac%3A1');
        $('#startOver').attr('href', url);
      }
    });

    $('#wb-sort-sub').click(function(event) {
      var controlForm = document.forms.mainForm;
      controlForm.submit();
    });

    $('#showSumLink').click(function(event) {
      event.preventDefault();
      var action = $('#showSum').val();
      if (langCode == 'fr') {
        showText = 'Afficher les résumés';
        hideText = 'Cacher les résumés';
      } else {
        showText = 'Show summaries';
        hideText = 'Hide summaries';
      }

      if (action == "hide" || action == "") {
        $("#showSumLink").text(showText);
        $("#showSum").val("show");
        $("#results .results_description").hide();
        $("#results hr.drk-grey").hide();
        $("span[data-name^='summary']").hide();
        $("span[data-name^='docdate']").hide();
        $("#results .results_description").hide();
      } else {
        $("#showSumLink").text(hideText);
        $("#showSum").val("hide");
          $("#results .results_description").show();
          $("#results hr.drk-grey").show();
          $("span[data-name^='summary']").show();
          $("span[data-name^='docdate']").show();

          $("#results .results_description").css('display', 'block');
          $("span[data-name^='summary']").css('display', 'block');
          $("span[data-name^='docdate']").css('display', 'block');
      }

      $("[id^='bcLink']").each(function() {
        var lll = $(this).attr("href");
        if (action == "hide") {
          lll = lll.replace("&showSum=hide","&showSum=show")
        } else {
          lll = lll.replace("&showSum=show","&showSum=hide")
        }
          $(this).attr("href",lll);
      });

      $("[id^='fctlink']").each(function() {
        var lll = $(this).attr("href");
        if (action == "hide") {
          lll = lll.replace("&showSum=hide","&showSum=show")
        }
        else {
          lll = lll.replace("&showSum=show","&showSum=hide")
        }
        $(this).attr("href",lll);
      });
    });

    $(".paginate_button,.prev-page,.next-page").click(function() {
      var startStr = $(this).attr("data-name");
      var startValArr = startStr.split("=");
      if (startValArr.length > 1) {
        $("#startVal").val(startValArr[1]);
      } else {
        $("#startVal").val(0);
      }
      $("#mainForm").submit();
    });
  });
})(jQuery);
