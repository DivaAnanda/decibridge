// Stored decimals carry ten places ("200.0000000000"); show them as typed.
// String-based on purpose: going through Number would round long values.
export function trimDecimal(value: string): string {
  return value.includes('.') ? value.replace(/\.?0+$/, '') : value
}
