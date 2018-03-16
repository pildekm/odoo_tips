odoo.define('website_sale.payment', function(require) {
	"use strict";
	var core = require('web.core');
	var _t = core._t;
	var ajax = require('web.ajax');
	var currentUrl = location.href;
	var title = $(document).find("title").text();
	$(document).ready(function() {
		$('.oe_website_upload').each(function(ev) {
			var oe_website_sale = this;
			ChangeUrl(title, currentUrl);
			$(oe_website_sale).on('click', 'a.file_browse_btn', function() {
				var data = $('input.file_browse').val();
				var $form = $(this).closest('form');
				$form.find('input[type="file"]').click();
			});

			// add attachment
			$(oe_website_sale).on('click', 'a.add-attachment', function() {
				$("#file_upload_modal").modal();
			});

			// view attachment
			$(oe_website_sale).on('click', 'a.view-attachment', function() {
				$('div.attachment-history').slideDown(500, function() {
					$('a.view-attachment').addClass('hide-attachment').removeClass('view-attachment');
					$('a.hide-attachment').html('&#032;Hide Attachment(s)');
				});

			});

			$(oe_website_sale).on('click', 'a.hide-attachment', function() {
				$('div.attachment-history').slideUp(500, function() {
					$('a.hide-attachment').addClass('view-attachment').removeClass('hide-attachment');
					$('a.view-attachment').html('&#032;View Attachment(s)');
				});

			});

			$(oe_website_sale).find('input[type="file"]').on('change', function() {
				var $form = $(this).closest('form');
				var name = $(this)[0].files[0].name;
				if ((!name) || name === '') {
					$('button.file_upload_btn').hide().addClass('disabled');
				} else {
					$('button.file_upload_btn').show().removeClass('disabled');
					$('div#file-upload-name').html('<span class="fa fa-file-o"></span>&#032;' + name);
				}
			});

			$(oe_website_sale).on('click', 'img.upload_hide_window', function() {
				$('div.attachment-history').slideUp(500, function() {
					$('img.upload_hide_window').hide();

				});
			});

			$(oe_website_sale).on('click', 'a#attachment-remove', function() {

				var $tbody = $(this).closest('tbody');
				var mc_id = parseInt($('#MC_id').val())
				var attachment_id = parseInt($tbody.find('input[name="attachment-id"]').first().val(), 10);
				ajax.jsonRpc("/certificate/remove_upload", 'call', {
						'attachment_id': attachment_id,
                        'mc_id': mc_id,
					})
					.then(function() {
						location.reload();
					});

			});

			function getPathFromUrl(url) {
				return url.split("?")[0];
			}

			function ChangeUrl(title, currentUrl) {
				if (currentUrl.indexOf("/shop/payment") != -1) {
					var newUrl = getPathFromUrl(currentUrl);
					var obj = {
						Title: title,
						Url: newUrl
					};
					history.pushState(obj, obj.Title, obj.Url);
				}
			}
		$('.wk_file_success').delay(3200).fadeOut(300);
		$('.wk_file_failed').delay(3200).fadeOut(300);
		});
	});
});