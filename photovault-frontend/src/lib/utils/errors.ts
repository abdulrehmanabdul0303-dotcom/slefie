// Error utilities
export function handleError(error: unknown) {
  console.error(error);
}

export function getErrorMessage(error: any): string {
  if (error?.response?.data?.detail) return error.response.data.detail;
  if (error?.message) return error.message;
  return "An error occurred";
}

