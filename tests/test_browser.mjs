import test from "node:test";
import assert from "node:assert/strict";
import {classify, parseTiter} from "../app.mjs";

test("parses paired IFA titer", () => assert.equal(parseTiter("1:256"), 256));
test("rejects nonquantitative titer", () => assert.throws(() => parseTiter("<1:16")));
test("identifies acute fourfold rise", () => assert.equal(classify(64, 256, 64).status, "acute_seroconversion_pattern"));
test("threefold rise is not diagnostic", () => assert.equal(classify(32, 192, 64).status, "single_sample_supportive"));
test("high phase I requires focus", () => assert.equal(classify(1024, 2048).status, "investigate_persistent_focus"));
test("persistent focus and high phase I", () => assert.equal(classify(1024, 8192, "", true).status, "persistent_pattern_with_focus"));
test("early negative not excluded", () => assert.equal(classify(0, 0).status, "insufficient_serologic_evidence"));
test("zero prior not fourfold", () => assert.equal(classify(0, 1024, 0).fourfold, false));
