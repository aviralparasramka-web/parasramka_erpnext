/**
 * PEPL Assistant — Frappe Page Controller
 * Option D: Chat interface backed by Claude AI via claude_integration.py
 */

frappe.pages["pepl-assistant"].on_page_load = function (wrapper) {
	const page = frappe.ui.make_app_page({
		parent: wrapper,
		title: "PEPL Assistant",
		single_column: true,
	});

	// Inject CSS
	frappe.require(
		frappe.boot.assets_json
			? []
			: [
					"/assets/parasramka_erpnext/css/pepl_assistant.css",
					// fallback: CSS loaded via page bundle
			  ]
	);

	// Render the HTML template into the page body
	$(frappe.render_template("pepl_assistant", {})).appendTo(page.body);

	// Initialise controller after DOM is ready
	new PEPLAssistant(wrapper);
};

class PEPLAssistant {
	constructor(wrapper) {
		this.wrapper     = wrapper;
		this.isLoading   = false;
		this.messageHistory = [];   // keep last N exchanges for UX context (not sent to Claude)

		this.$chatWindow  = wrapper.find("#chat-window");
		this.$input       = wrapper.find("#chat-input");
		this.$sendBtn     = wrapper.find("#send-btn");
		this.$statusDot   = wrapper.find("#status-dot");
		this.$statusText  = wrapper.find("#status-text");
		this.$chips       = wrapper.find("#suggestion-chips");

		this._bindEvents();
	}

	// ── Event binding ─────────────────────────────────────────────────────────

	_bindEvents() {
		// Send on button click
		this.$sendBtn.on("click", () => this._handleSend());

		// Send on Ctrl+Enter
		this.$input.on("keydown", (e) => {
			if (e.ctrlKey && e.key === "Enter") {
				e.preventDefault();
				this._handleSend();
			}
		});

		// Auto-resize textarea
		this.$input.on("input", () => {
			const el = this.$input[0];
			el.style.height = "auto";
			el.style.height = Math.min(el.scrollHeight, 120) + "px";
		});

		// Suggestion chip clicks
		this.$chips.on("click", ".pepl-chip", (e) => {
			const question = $(e.currentTarget).data("q");
			this.$input.val(question);
			this._handleSend();
		});
	}

	// ── Send flow ─────────────────────────────────────────────────────────────

	_handleSend() {
		const question = (this.$input.val() || "").trim();
		if (!question || this.isLoading) return;

		// Clear input immediately
		this.$input.val("").css("height", "auto");

		// Render user bubble
		this._appendBubble("user", question);

		// Show typing indicator
		const $typing = this._appendTypingIndicator();

		// Update status
		this._setLoading(true);

		// Call the backend API
		frappe.call({
			method: "parasramka_erpnext.parasramka_erpnext.api.claude_integration.query_erpnext_data",
			args: { question },
			callback: (r) => {
				$typing.remove();
				if (r.message) {
					this._appendBubble("assistant", r.message);
				} else {
					this._appendErrorBubble("No response received from the assistant.");
				}
			},
			error: (r) => {
				$typing.remove();
				const msg =
					r.exception ||
					r._server_messages ||
					"Failed to reach PEPL Assistant. Please check the API configuration.";
				this._appendErrorBubble(_clean_error(msg));
			},
		}).always(() => {
			this._setLoading(false);
		});
	}

	// ── DOM helpers ───────────────────────────────────────────────────────────

	_appendBubble(role, text) {
		const isUser = role === "user";
		const avatar = isUser ? frappe.session.user_email.charAt(0).toUpperCase() : "AI";
		const time   = frappe.datetime.now_time();
		const html   = `
			<div class="pepl-bubble ${role}">
				<div class="pepl-bubble-avatar">${avatar}</div>
				<div>
					<div class="pepl-bubble-body">${_formatText(text)}</div>
					<div class="pepl-timestamp">${time}</div>
				</div>
			</div>
		`;
		const $el = $(html).appendTo(this.$chatWindow);
		this._scrollToBottom();
		return $el;
	}

	_appendErrorBubble(message) {
		const html = `
			<div class="pepl-bubble error">
				<div class="pepl-bubble-avatar">!</div>
				<div class="pepl-bubble-body">
					⚠️ ${frappe.utils.escape_html(message)}
				</div>
			</div>
		`;
		$(html).appendTo(this.$chatWindow);
		this._scrollToBottom();
	}

	_appendTypingIndicator() {
		const html = `
			<div class="pepl-bubble assistant" id="typing-indicator">
				<div class="pepl-bubble-avatar">AI</div>
				<div class="pepl-bubble-body pepl-typing">
					<span></span><span></span><span></span>
				</div>
			</div>
		`;
		const $el = $(html).appendTo(this.$chatWindow);
		this._scrollToBottom();
		return $el;
	}

	_scrollToBottom() {
		const el = this.$chatWindow[0];
		el.scrollTop = el.scrollHeight;
	}

	_setLoading(state) {
		this.isLoading = state;
		this.$sendBtn.prop("disabled", state);

		if (state) {
			this.$statusDot.addClass("loading");
			this.$statusText.text("Thinking…");
		} else {
			this.$statusDot.removeClass("loading");
			this.$statusText.text("Ready");
		}
	}
}

// ── Utility functions ─────────────────────────────────────────────────────────

/** Convert plain text (with newlines and basic markdown) to safe HTML. */
function _formatText(text) {
	// Escape HTML first
	let html = frappe.utils.escape_html(text);
	// Restore code blocks
	html = html.replace(/`([^`]+)`/g, "<code>$1</code>");
	// Bold
	html = html.replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");
	// Bullet list lines starting with "- " or "• "
	html = html.replace(/^[-•]\s(.+)$/gm, "<li>$1</li>");
	html = html.replace(/(<li>.*<\/li>)/s, "<ul>$1</ul>");
	// Numbered list
	html = html.replace(/^\d+\.\s(.+)$/gm, "<li>$1</li>");
	// Paragraph breaks
	html = html
		.split(/\n{2,}/)
		.map((para) => `<p>${para.replace(/\n/g, "<br>")}</p>`)
		.join("");
	return html;
}

/** Strip frappe server_messages JSON wrapper if present. */
function _clean_error(msg) {
	try {
		const parsed = JSON.parse(msg);
		if (Array.isArray(parsed)) {
			return parsed.map((m) => {
				try { return JSON.parse(m).message || m; }
				catch { return m; }
			}).join(" ");
		}
	} catch (_) {
		// not JSON — return as-is
	}
	return String(msg).substring(0, 300);
}
