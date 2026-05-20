import apiClient from './client';

export interface Printer {
  id: string;
  name: string;
  printer_type: string;
  ip_address: string | null;
  port: number;
  paper_width: number;
  is_active: boolean;
}

export interface PrintRequest {
  printer_id: string;
  job_type: 'kot' | 'bill' | 'receipt';
  order_data: Record<string, unknown>;
}

export const printersApi = {
  list: (branchId?: string) => {
    const params: Record<string, string> = {};
    if (branchId) params.branch_id = branchId;
    return apiClient.get<Printer[]>('/printers/', { params });
  },

  print: (data: PrintRequest) =>
    apiClient.post<{ job_id: string; status: string }>('/printers/print', data),
};
