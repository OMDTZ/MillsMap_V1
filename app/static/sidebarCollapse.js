//TODO: package as functions

$(document).ready(function () {
    $('#sidebarCollapse').on('click', function () {
        $('#sidebar').toggleClass('hide');
        $('#mapbar').toggleClass('col-8');
        $('#left-arrow').toggleClass('hide');
        $('#right-arrow').toggleClass('hide');
    });
});

$(document).ready(function () {
    $('#sidebarOpen').on('click', function () {
        $('#sidebar').toggleClass('hide');
        $('#mapbar').toggleClass('col-8');
        $('#left-arrow').toggleClass('hide');
        $('#right-arrow').toggleClass('hide');
    });

});
