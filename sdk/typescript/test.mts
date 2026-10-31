import assert from 'node:assert/strict';
import {Coulis, CoulisError} from './src/index.ts';
const api = new Coulis(process.argv[2], 'key-a');
const edit = await api.workflow('edit', {task:'Launch',draft:'Thrilled',final:'We built this',context:{surface:'x'},category:'style',consent:true});
const proposal = await api.workflow('propose', {comparison_id:edit.id,key:'tone',value:'direct',wording:'Be direct'});
await api.workflow('approve', {proposal_id:proposal.id,approved:true});
const context = await api.context('Another topic','x');
assert.equal(context.preferences[0].id,proposal.id);
const other = new Coulis(process.argv[2],'key-b');
assert.deepEqual((await other.context('Another topic','x')).preferences, []);
await assert.rejects(new Coulis(process.argv[2], 'wrong').workflow('state'), (e:any) => e instanceof CoulisError && e.status===401);
await api.workflow('purge', {approved:true});
assert.deepEqual((await api.workflow('state')).preferences, []);

const structural = await api.workflow('edit', {task:'Post',draft:'We build tools — we learn from the people who use them.',final:'We build tools, we learn from the people who use them.',context:{surface:'x'},category:'style',consent:true});
const extracted = await api.workflow('extract', {comparison_id:structural.id});
assert.equal(extracted.proposals[0].value, 'avoid');
assert.equal(extracted.proposals[0].approved, false);
