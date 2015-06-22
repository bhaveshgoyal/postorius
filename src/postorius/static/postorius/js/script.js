$(document).ready(function() {
	$('[name="query_field"]').attr("list","global-result");
	$("#id_query_field").attr("placeholder", "Search Dashboard");
	$("#id_query_field").on('input', function(){
		$("#global-search-form").submit();
		var val = this.value;
		$('#global-result option').each(function(){
			if (this.value === val){
				if ($(this).attr("id") == "list_option"){
					window.location = "/postorius/lists/" + $(this).attr("label");
				}
				else if ($(this).attr("id") == "people_option"){
					window.location = "/postorius/lists/" + $(this).attr("label") + "/members";
				}
				else if ($(this).attr("id") == "domain_option"){
					window.location = "/postorius/domains";
				}
			}
		}); 
	});
	$("#global-search-form").submit(function() {
		var myCheckboxes = new Array();
		$("input:checked").each(function() {
			myCheckboxes.push($(this).val());
		});
		$.ajax({
			type: "POST",
			url: $("[name='dashboard_url']").val(),
			data: $(this).serialize(),
			success: function(response){
				$("#global-result").empty();
				for (each in response.lists){
					var id = response.lists[each].list_id
					$("#global-result").append("<option id='list_option' value='" + response.lists[each].display_name + "' label='" + response.lists[each].list_id + "'>");
				}
				for (each in response.people){
					$("#global-result").append("<option id='people_option' value='" + response.people[each].useremail + "' label='" + response.people[each].list_id + "'>");
				}
				for (each in response.domains){
					$("#global-result").append("<option id='domain_option' value='" + response.domains[each].mail_host + "' label='" + response.domains[each].base_url + "'>");
				}
			}
		});
		return false;
	});



		$('#select-list').multiselect({
			onChange: function(option, checked, select) {
				var lists = []
				$('#select-list option:selected').each(function(idx, val){lists.push(val.value);});	
				var data = {csrfmiddlewaretoken: document.getElementsByName('csrfmiddlewaretoken')[0].value, selected_lists : lists};
				$.ajax({
					type: "POST",
					url: $("[name='dashboard_url']").val(),
					data: data,
					success: function(response){
						subs = response.subs
						mods = response.mods
						var subs_data = []
						var mods_data = []
						var dates = []
						for (each in subs){
							dates.push(each)
			   				subs_data.push(subs[each])
							mods_data.push(mods[each])
					   	 }
				    		dates.push("")
						subs_data.push("")
						mods_data.push("")
						var chart = new Chartist.Line('.ct-chart', {
							labels: dates,
							series: [{
									name: 'Moderation Requests',
									data: mods_data

								},
								{
									name: 'Subscription Requests',
									data:  subs_data
								}]
						}, {
							low: 0,
							axisX: {
								offset: 25,
								labelOffset: { y: 10 }
								},
							axisY: {
								offset: 35,
								labelOffset: { x: -10,y: 3 }
								},			     
							lineSmooth: Chartist.Interpolation.simple({
								divisor: 5
						        }),
							fullWidth: true
						});
					}
				});
			}
		});

console.log($("[name='dates']"));
var dates = $("[name='dates']").val().split(",");
var subs_data = $("[name='subs_data']").val().split(",");
var mods_data = $("[name='mods_data']").val().split(",");
var chart = new Chartist.Line('.ct-chart', {
	labels: dates,
	series: [
	{
		name: 'Moderation Requests',
		data: mods_data
	
	},
	{
		name: 'Subscription Requests',
		data:  subs_data
		}]
		}, {
			low: 0,
			axisX: {
				offset: 25,
				labelOffset: { y: 10 }
				},
			axisY: {
				offset: 35,
				labelOffset: { x: -10,y: 3 }
				},
			     
			lineSmooth: Chartist.Interpolation.simple({
				divisor: 5
		        }),
			 fullWidth: true
			     
		});


var $tooltip = $('<div class="tooltip tooltip-hidden"></div>').appendTo($('.ct-chart'));
 
$(document).on('mouseenter', '.ct-point', function() {
	var seriesName = $(this).closest('.ct-series').attr('ct:series-name'),
	value = $(this).attr('ct:value');	  
	$tooltip.text(seriesName + ': ' + value);
	$tooltip.removeClass('tooltip-hidden');
});

$(document).on('mouseleave', '.ct-point', function() {
	$tooltip.addClass('tooltip-hidden');
});

$(document).on('mousemove', '.ct-point', function(event) {
	$tooltip.css({
		left: (event.offsetX || event.originalEvent.layerX) - $tooltip.width() / 2,
		top: (event.offsetY || event.originalEvent.layerY) - $tooltip.height() - 20
	});
});

$("#switcher a").on("click", function(){
	$(".nav").find(".active").removeClass("active");
	$(this).parent().addClass("active");
	var id = $(".nav").find(".active").children().attr("id");
	if (id == 'list-view'){
		$("#task-container").hide("fast");
		$("#reorder").hide("fast");
		$("#list-container").show("fast");
	}
	else if (id == 'task-view'){
		$("#list-container").hide("fast");
		$("#reorder").show("fast");
		$("#task-container").show("fast");
	}
});
$("#parent-per-list a").on("click", function(){
	$(".parent-list-nav").find(".parent-active").removeClass("parent-active");
	$(this).parent().addClass("parent-active");
	var mod_badges = $(".mod-badge");
	var sub_badges = $(".sub-badge");
	var both_badges = $(".both-badge");

	$(".panel_lists").hide();
	var badge_id = $("#parent-per-list").find(".parent-active").attr("id");
	var par_cont = $(this).parents('#list-container')
	if (badge_id == 'both'){
		mod_badges.each(function(){$(this).hide();});
		sub_badges.each(function(){$(this).hide();});
		both_badges.each(function(){$(this).show();});
			
		$(par_cont).find(".per-list-nav").show();
		var active_tab = $(par_cont).find(".per-list-nav").children('.active').attr("id")
		if (!active_tab){
			$(par_cont).find("#list-subscriptions").hide();
			$(par_cont).find("#list-moderations").show();
		}
		else if (active_tab == 'list-mod'){
			$(par_cont).find("#list-subscriptions").hide();
			$(par_cont).find("#list-moderations").show();
		}
		else if (active_tab == 'list-sub'){
			$(par_cont).find("#list-subscriptions").show();
			$(par_cont).find("#list-moderations").hide();
		}
	}
	else if (badge_id == 'modr'){
		mod_badges.each(function(){$(this).show();});
		sub_badges.each(function(){$(this).hide();});
		both_badges.each(function(){$(this).hide();});
		
		$(par_cont).find(".per-list-nav").hide();
		$(par_cont).find("#list-subscriptions").hide();
		$(par_cont).find("#list-moderations").show();

	}
	if (badge_id == 'subr'){
		mod_badges.each(function(){$(this).hide();});
		sub_badges.each(function(){$(this).show();});
		both_badges.each(function(){$(this).hide();});
			
		$(par_cont).find(".per-list-nav").hide();
		$(par_cont).find("#list-subscriptions").show();
		$(par_cont).find("#list-moderations").hide();
	}
	$(".panel_lists").fadeIn();
});
$(".per-list-nav a").on("click", function(){
	var parent_ul = $(this).parents('ul.per-list-nav').children('.active').removeClass("active");
	$(this).parents('li').addClass("active");
	var id = $(this).parents('ul.per-list-nav').children('.active').attr("id");
	var par = $(this).parents('.panel-body');
	if (id == 'list-mod'){
		$(par).children('#list-subscriptions').hide("fast");
		$(par).children('#list-moderations').show("fast");
	}
	else if (id == 'list-sub'){
		$(par).children('#list-subscriptions').show("fast");
		$(par).children('#list-moderations').hide("fast");
	}
});
$(".role-nav a").on("click", function(){
	var parent_ul = $(this).parents('ul.role-nav').children('.active').removeClass("active");
	$(this).parents('li').addClass("active");
	var id = $(this).parents('ul.role-nav').children('.active').attr("id");
	var par = $(this).parents('.panel-body');
	if (id == 'role-moderators'){
		$(par).children('#list-owners').hide("fast");
		$(par).children('#list-subscribers').hide("fast");
		$(par).children('#list-moderators').show("fast");
	}
	else if (id == 'role-owners'){
		$(par).children('#list-moderators').hide("fast");
		$(par).children('#list-owners').show("fast");
		$(par).children('#list-subscribers').hide("fast");
	}
	else if (id == 'role-subscribers'){
		$(par).children('#list-owners').hide("fast");
		$(par).children('#list-subscribers').show("fast");
		$(par).children('#list-moderators').hide("fast");
	}
});

$('.remove-role .remove').click(function(){
	return false;
});

$('.remove-role .remove').dblclick(function(){
	var href = $(this).attr("href");
	window.location = href;
});
});
