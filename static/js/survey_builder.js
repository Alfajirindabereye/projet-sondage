(function () {
  var container = document.getElementById('questions-container');
  var template = document.getElementById('question-template');
  var addBtn = document.getElementById('add-question-btn');

  function blocks() {
    return Array.prototype.slice.call(container.querySelectorAll('[data-block]'));
  }

  function addRow(data) {
    data = data || {};
    var node = template.content.firstElementChild.cloneNode(true);
    container.appendChild(node);

    var textInput = node.querySelector('[data-text]');
    var typeSelect = node.querySelector('[data-type]');
    var choicesGroup = node.querySelector('[data-choices-group]');
    var choicesTextarea = node.querySelector('[data-choices]');
    var requiredCheckbox = node.querySelector('[data-required-checkbox]');
    var requiredHidden = node.querySelector('[data-required-hidden]');
    var conditionToggle = node.querySelector('[data-condition-toggle]');
    var conditionBox = node.querySelector('[data-condition-box]');
    var conditionQuestionSelect = node.querySelector('[data-condition-question]');
    var conditionChoiceSelect = node.querySelector('[data-condition-choice]');
    var conditionIndexHidden = node.querySelector('[data-condition-index-hidden]');
    var conditionChoiceHidden = node.querySelector('[data-condition-choice-hidden]');
    var removeBtn = node.querySelector('[data-remove]');

    textInput.value = data.text || '';
    typeSelect.value = data.type || 'single';
    choicesTextarea.value = (data.choices || []).join('\n');
    requiredCheckbox.checked = data.required !== false;
    requiredHidden.value = requiredCheckbox.checked ? '1' : '0';

    toggleChoicesVisibility(typeSelect, choicesGroup);

    typeSelect.addEventListener('change', function () {
      toggleChoicesVisibility(typeSelect, choicesGroup);
      refreshAllConditionDropdowns();
    });
    choicesTextarea.addEventListener('input', refreshAllConditionDropdowns);
    textInput.addEventListener('input', refreshAllConditionDropdowns);
    requiredCheckbox.addEventListener('change', function () {
      requiredHidden.value = requiredCheckbox.checked ? '1' : '0';
    });

    removeBtn.addEventListener('click', function () {
      node.remove();
      renumber();
      refreshAllConditionDropdowns();
    });

    conditionToggle.addEventListener('change', function () {
      conditionBox.style.display = conditionToggle.checked ? 'block' : 'none';
      if (!conditionToggle.checked) {
        conditionQuestionSelect.value = '';
        conditionChoiceSelect.innerHTML = '<option value="">— choisir une réponse —</option>';
        conditionIndexHidden.value = '';
        conditionChoiceHidden.value = '';
      }
    });

    conditionQuestionSelect.addEventListener('change', function () {
      conditionIndexHidden.value = conditionQuestionSelect.value;
      populateChoiceOptions(conditionQuestionSelect, conditionChoiceSelect);
      conditionChoiceHidden.value = '';
    });
    conditionChoiceSelect.addEventListener('change', function () {
      conditionChoiceHidden.value = conditionChoiceSelect.value;
    });

    renumber();
    refreshAllConditionDropdowns();

    // Prefill condition data after DOM + dropdown structure exist
    if (data.condition_index !== null && data.condition_index !== undefined && data.condition_choice_text) {
      conditionToggle.checked = true;
      conditionBox.style.display = 'block';
      window.setTimeout(function () {
        conditionQuestionSelect.value = String(data.condition_index);
        conditionIndexHidden.value = String(data.condition_index);
        populateChoiceOptions(conditionQuestionSelect, conditionChoiceSelect);
        conditionChoiceSelect.value = data.condition_choice_text;
        conditionChoiceHidden.value = data.condition_choice_text;
      }, 0);
    }

    return node;
  }

  function toggleChoicesVisibility(typeSelect, choicesGroup) {
    choicesGroup.style.display = typeSelect.value === 'text' ? 'none' : 'block';
  }

  function renumber() {
    blocks().forEach(function (b, i) {
      b.querySelector('[data-index-label]').textContent = 'Question ' + (i + 1);
    });
  }

  function refreshAllConditionDropdowns() {
    var rows = blocks();
    rows.forEach(function (b, i) {
      var select = b.querySelector('[data-condition-question]');
      var currentVal = select.value;
      var options = ['<option value="">— choisir une question —</option>'];
      rows.forEach(function (other, j) {
        if (j >= i) return; // only questions that appear before this one
        var t = other.querySelector('[data-text]').value.trim() || ('Question ' + (j + 1));
        options.push('<option value="' + j + '">' + escapeHtml(t) + '</option>');
      });
      select.innerHTML = options.join('');
      if (currentVal !== '' && select.querySelector('option[value="' + currentVal + '"]')) {
        select.value = currentVal;
      }
    });
  }

  function populateChoiceOptions(conditionQuestionSelect, conditionChoiceSelect) {
    var idx = conditionQuestionSelect.value;
    conditionChoiceSelect.innerHTML = '<option value="">— choisir une réponse —</option>';
    if (idx === '') return;
    var rows = blocks();
    var targetRow = rows[parseInt(idx, 10)];
    if (!targetRow) return;
    var lines = targetRow.querySelector('[data-choices]').value.split('\n').map(function (l) { return l.trim(); }).filter(Boolean);
    lines.forEach(function (line) {
      var opt = document.createElement('option');
      opt.value = line;
      opt.textContent = line;
      conditionChoiceSelect.appendChild(opt);
    });
  }

  function escapeHtml(str) {
    var div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
  }

  addBtn.addEventListener('click', function () {
    addRow();
  });

  // Initial population
  var prefill = window.SURVEY_PREFILL || [];
  if (prefill.length) {
    prefill.forEach(function (row) { addRow(row); });
  } else {
    addRow();
  }
})();
