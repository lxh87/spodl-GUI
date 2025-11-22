import { create } from 'zustand';
import type { QueueState } from '../types/spotdl';

export const useQueueStore = create<QueueState>((set) => ({
  items: [],

  addItem: (item) =>
    set((state) => ({
      items: [
        ...state.items,
        {
          ...item,
          id: crypto.randomUUID(),
          status: 'queued',
          progress: 0,
        },
      ],
    })),

  removeItem: (id) =>
    set((state) => ({
      items: state.items.filter((item) => item.id !== id),
    })),

  updateItem: (id, updates) =>
    set((state) => ({
      items: state.items.map((item) =>
        item.id === id ? { ...item, ...updates } : item
      ),
    })),

  clearCompleted: () =>
    set((state) => ({
      items: state.items.filter((item) => item.status !== 'completed'),
    })),

  clearAll: () => set({ items: [] }),
}));
