import assert from 'node:assert/strict';
import test from 'node:test';
import { maskPinfl, paymentStatus, remainingAmount } from '../src/utils/student.js';

test('remainingAmount manfiy bo‘lmaydi', () => {
  assert.equal(remainingAmount(1000, 1200), 0);
});

test('paymentStatus to‘g‘ri qiymat qaytaradi', () => {
  assert.equal(paymentStatus(1000, 0), 'TO‘LANMAGAN');
  assert.equal(paymentStatus(1000, 600), 'QISMAN TO‘LANGAN');
  assert.equal(paymentStatus(1000, 1000), 'TO‘LIQ TO‘LANGAN');
});

test('maskPinfl oxirgi 4 raqamni qoldiradi', () => {
  assert.equal(maskPinfl('12345678901234'), '**********1234');
});
