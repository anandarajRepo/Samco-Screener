$(document).ready(function () {

    $("#stocktable tr").click(function() {
        $(this).toggleClass("table-secondary");
    });

    $("#alert-favourite").hide();
    $('input[name="insturmentId"]').click(function () {
        var stockId;
        if ($(this).is(":checked")) {
            console.log('Checked');
            console.log($(this).val());
            stockId = $(this).val();
            $.ajax({
                method: "POST",
                url: "/insert",
                data: { 'data': $(this).val(), 'event': true },
                cache: false,
                success: function (data) {
                    $("#result-success").html(data);
                    $("#alert-favourite-success").alert();
                    $("#alert-favourite-success").fadeTo(2000, 500).slideUp(500, function () {
                        $("#alert-favourite-success").slideUp(500);
                    });
                    $("#success-alert-success").alert('close');
                }
            });
        } else {
            console.log('Unchecked');
            console.log($(this).val());
            stockId = $(this).val();
            $.ajax({
                method: "POST",
                url: "/insert",
                data: { 'data': $(this).val(), 'event': false },
                cache: false,
                success: function (data) {
                    $("#result-warning").html(data);
                    $("#alert-favourite-warning").alert();
                    $("#alert-favourite-warning").fadeTo(2000, 500).slideUp(500, function () {
                        $("#alert-favourite-warning").slideUp(500);
                    });
                    $("#success-alert-warning").alert('close');
                }
            });
        }

    });

});