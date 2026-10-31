"""Conservative edit-feature proposals. No model calls or calibrated confidence claims."""
import re

VERSION = 'edit-features-v1'


def extract(draft, final):
    """Only describes observable style changes; caller must supply explicit style evidence."""
    numbers = lambda s: re.findall(r'\b\d+(?:[.,]\d+)*%?', s)
    if numbers(draft) != numbers(final):
        return [], 'Numbers changed: separate factual corrections before extracting taste.'
    if draft == final:
        return [], 'No change.'
    words = lambda s: re.findall(r"\b[\w’']+\b", s)
    dw, fw = words(draft), words(final)
    if len(dw) < 8 or len(fw) < 8:
        return [], 'Too little text for these conservative style heuristics.'
    candidates = []
    def add(key, value, wording, before, after):
        candidates.append({'key':key,'value':value,'wording':wording,
            'observation':{'before':before,'after':after},
            'confidence':None,'confidence_label':'tentative_single_edit',
            'warning':'One edit is evidence of a choice, not a stable general preference.'})
    # Require unchanged lexical content for punctuation/casing/layout inferences.
    same_words = [w.casefold() for w in dw] == [w.casefold() for w in fw]
    if same_words:
        if draft.count('—') and not final.count('—'):
            add('punctuation.em_dash','avoid','Avoid em dashes in this context.',draft.count('—'),0)
        elif final.count('—') and not draft.count('—'):
            add('punctuation.em_dash','allow','Use em dashes when they fit in this context.',0,final.count('—'))
        if draft.lower()!=draft and final.lower()==final:
            add('casing','lowercase','Use lowercase in this context.','mixed case','lowercase')
        dp, fp = len(re.split(r'\n\s*\n',draft.strip())), len(re.split(r'\n\s*\n',final.strip()))
        if dp != fp:
            add('layout.paragraphs','more' if fp>dp else 'fewer',
                'Use more paragraph breaks.' if fp>dp else 'Use fewer paragraph breaks.',dp,fp)
        sentences = lambda s: max(1,len([x for x in re.split(r'[.!?]+(?:\s|$)',s) if x.strip()]))
        ds, fs = sentences(draft), sentences(final)
        if fs >= ds+1 and len(dw)/ds >= 12 and len(fw)/fs <= len(dw)/ds*.8:
            add('rhythm.sentences','shorter','Prefer shorter sentences in this context.',round(len(dw)/ds,2),round(len(fw)/fs,2))
    return candidates[:3], None if candidates else 'No reliable structural proposal. Use a human-reviewed semantic proposal instead.'
