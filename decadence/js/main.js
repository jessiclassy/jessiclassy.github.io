(function($) {
  "use strict"; // Start of use strict

  
  // Closes responsive menu when a scroll trigger link is clicked
  $('.js-scroll-trigger').click(function() {
    $('.navbar-collapse').collapse('hide');
  });

  // Activate scrollspy to add active class to navbar items on scroll
  $('body').scrollspy({
    target: '#mainNav',
    offset: 56
  });

  $('.close-modal').click(function(e) {
    $('.member-modal').modal('hide');
    $(document.body).addClass('test');
  });


  $(function () {
    $('[data-bm-close][data-bm-open]').on('click', function () {
      var $this = $(this);
      $($this.data('bm-close')).one('hidden.bs.modal', function () {
          $($this.data('bm-open')).modal('show');
      }).modal('hide');
    });
  });

})(jQuery); // End of use strict


