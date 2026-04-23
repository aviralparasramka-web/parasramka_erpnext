/**
 * Quotation — "Draft with Claude" button
 * Calls claude_integration.draft_letter() and shows
 * the AI-drafted letter text in a dialog for review/copy.
 */

frappe.ui.form.on("Quotation", {
	refresh(frm) {
		// Only show when the quotation is saved (not new) and not cancelled
		if (frm.doc.docstatus === 2 || frm.doc.__islocal) return;

		frm.add_custom_button(
			__("Draft with Claude"),
			() => _showDraftDialog(frm),
			__("AI")   // group the button under an "AI" dropdown
		);

		// Apply a subtle accent colour to the AI button group
		frm.page.btn_secondary
			.find('.btn-group [data-label="AI"]')
			.addClass("btn-warning");
	},
});

// ── Dialog: pick letter type and run ─────────────────────────────────────────

function _showDraftDialog(frm) {
	const letterTypes = [
		"Quotation Letter",
		"Payment Request",
		"Down Payment Request",
		"Drawing Request",
		"Lot Offer",
	];

	const dialog = new frappe.ui.Dialog({
		title: __("Draft Letter with Claude AI"),
		fields: [
			{
				label:     __("Letter Type"),
				fieldname: "letter_type",
				fieldtype: "Select",
				options:   letterTypes.join("\n"),
				default:   "Quotation Letter",
				reqd:      1,
				description: __("Choose the type of letter you want Claude to draft."),
			},
			{
				label:     __("Document Reference"),
				fieldname: "document_name",
				fieldtype: "Data",
				default:   frm.doc.name,
				reqd:      1,
				description: __(
					"The ERPNext document name to base the letter on (auto-filled from current Quotation)."
				),
			},
			{
				fieldtype: "HTML",
				fieldname: "info_html",
				options: `<div style="padding:8px 0;color:#5e6c84;font-size:12px;">
					Claude will fetch the document data and draft a professional letter body.
					You can edit the result before using it.
				</div>`,
			},
		],
		primary_action_label: __("Generate Draft"),
		primary_action(values) {
			dialog.disable_primary_action();
			dialog.set_title(__("Generating… please wait"));
			_runDraft(values.letter_type, values.document_name, dialog);
		},
	});

	dialog.show();
}

// ── Call backend and show result ──────────────────────────────────────────────

function _runDraft(letterType, documentName, sourceDialog) {
	frappe.call({
		method:
			"parasramka_erpnext.parasramka_erpnext.api.claude_integration.draft_letter",
		args: {
			letter_type:   letterType,
			document_name: documentName,
		},
		callback(r) {
			sourceDialog.hide();
			if (r.message) {
				_showResultDialog(letterType, r.message);
			} else {
				frappe.msgprint({
					title:   __("Claude returned no content"),
					message: __("The API call succeeded but returned an empty response."),
					indicator: "orange",
				});
			}
		},
		error(r) {
			sourceDialog.enable_primary_action();
			sourceDialog.set_title(__("Draft Letter with Claude AI"));
			const msg =
				r.exc ||
				r._server_messages ||
				__("An error occurred while calling the Claude API.");
			frappe.msgprint({
				title:     __("Claude API Error"),
				message:   _extractError(msg),
				indicator: "red",
			});
		},
	});
}

// ── Result dialog with editable text area ────────────────────────────────────

function _showResultDialog(letterType, draftText) {
	const resultDialog = new frappe.ui.Dialog({
		title:  __("Claude Draft — {0}", [letterType]),
		size:   "large",
		fields: [
			{
				fieldtype:   "Small Text",
				fieldname:   "draft_body",
				label:       __("Drafted Letter Body"),
				default:     draftText,
				description: __(
					"Review and edit this text. Copy it into your letter template or print format."
				),
			},
			{
				fieldtype: "HTML",
				fieldname: "actions_html",
				options:   _buildActionHTML(),
			},
		],
		primary_action_label: __("Copy to Clipboard"),
		primary_action(values) {
			_copyToClipboard(values.draft_body);
			frappe.show_alert({ message: __("Copied to clipboard!"), indicator: "green" }, 3);
		},
	});

	resultDialog.show();

	// Resize the textarea to show full content
	setTimeout(() => {
		const $ta = resultDialog.fields_dict.draft_body.$input;
		if ($ta) {
			$ta.css({ "min-height": "320px", "font-family": "monospace", "font-size": "13px" });
		}
	}, 100);
}

// ── Helpers ───────────────────────────────────────────────────────────────────

function _buildActionHTML() {
	return `
		<div style="padding:8px 0;color:#5e6c84;font-size:12px;line-height:1.6;">
			<strong>Next steps:</strong><br>
			1. Edit the letter body above as needed.<br>
			2. Copy it and paste into a new Communication or Email Compose.<br>
			3. Add it to a print format or send directly from ERPNext.
		</div>
	`;
}

function _copyToClipboard(text) {
	if (navigator.clipboard) {
		navigator.clipboard.writeText(text);
	} else {
		// Fallback for older browsers
		const $tmp = $("<textarea>").val(text).appendTo("body");
		$tmp[0].select();
		document.execCommand("copy");
		$tmp.remove();
	}
}

function _extractError(msg) {
	try {
		const parsed = JSON.parse(msg);
		if (Array.isArray(parsed)) {
			return parsed
				.map((m) => { try { return JSON.parse(m).message || m; } catch { return m; } })
				.join(" ");
		}
	} catch (_) {
		// not JSON
	}
	return String(msg).substring(0, 500);
}
