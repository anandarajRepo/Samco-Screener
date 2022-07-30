$(document).ready(function () {

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
                    $("#result").html(data);
                    $("#alert-favourite").fadeTo(2000, 500).slideUp(500, function () {
                        $("#alert-favourite").slideUp(500);
                    });
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
                    $("#result").html(data);
                    $("#alert-favourite").fadeTo(2000, 500).slideUp(500, function () {
                        $("#alert-favourite").slideUp(500);
                    });
                }
            });
        }

    });

    $('#sector-dropdown').on('change', function () {
        $("#sub-category-dropdown").html("");
        var sectorName = $(this).val();
        console.log(sectorName)
        $.ajax({
            url: "/fetchSubSector",
            type: "POST",
            data: {
                sectorName: sectorName
            },
            cache: false,
            success: function (data) {
                var output = "";
                console.log(data.subsector)
                output += "<option value=''>Choose Sub-Sector</option>"
                $.each(data.subsector, function (key, val) {
                    output += "<option value='" + val + "'>" + val + "</option>"
                });
                $("#sub-category-dropdown").append(output);
            }
        });
    });



});