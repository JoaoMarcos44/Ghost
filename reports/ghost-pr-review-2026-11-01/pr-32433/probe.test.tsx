import React, { useState } from 'react';
import { act, cleanup, renderHook } from '@testing-library/react';
import useHeadGroup from './head/use-setting-group';
import useBaseGroup from './base/use-setting-group';
import { useDesignForm as useHeadDesign } from './head/use-design-form';
import { useDesignForm as useBaseDesign } from './base/use-design-form';
import { GlobalContext, editSettings, setGlobalDirtyState, type Setting } from './shared';

function deferred<T>() {
  let resolve!: (value: T) => void;
  const promise = new Promise<T>((done) => { resolve = done; });
  return { promise, resolve };
}

function provider(initialSettings: Setting[]) {
  let setSettings!: (settings: Setting[]) => void;
  const Wrapper = ({ children }: { children: React.ReactNode }) => {
    const [settings, changeSettings] = useState(initialSettings);
    setSettings = changeSettings;
    return <GlobalContext.Provider value={{ settings }}>{children}</GlobalContext.Provider>;
  };
  return { Wrapper, refresh: (settings: Setting[]) => setSettings(settings) };
}

const implementations = [
  { name: 'head', group: useHeadGroup, design: useHeadDesign, head: true },
  { name: 'base', group: useBaseGroup, design: useBaseDesign, head: false },
];

beforeEach(() => {
  vi.useFakeTimers();
  editSettings.mockReset();
  setGlobalDirtyState.mockReset();
});
afterEach(() => {
  cleanup();
  vi.clearAllTimers();
  vi.useRealTimers();
});

describe.each(implementations)('$name', ({ group, design, head }) => {
  it('keeps a later edit and the editor open after a stale save only at head', async () => {
    const request = deferred<void>();
    const data = provider([{ key: 'title', value: 'Original' }]);
    editSettings.mockReturnValue(request.promise);
    const { result } = renderHook(() => group(), { wrapper: data.Wrapper });
    act(() => { result.current.handleEditingChange(true); result.current.updateSetting('title', 'A'); });
    let first!: Promise<boolean>;
    act(() => { first = result.current.handleSave(); });
    act(() => result.current.updateSetting('title', 'B'));
    act(() => data.refresh([{ key: 'title', value: 'A' }]));
    expect(result.current.localSettings[0].value).toBe('B');
    let returned!: boolean;
    await act(async () => { request.resolve(); returned = await first; });
    expect(returned).toBe(!head);
    expect(result.current.isEditing).toBe(head);
    expect(result.current.saveState).toBe(head ? 'unsaved' : 'saved');
    expect(result.current.localSettings[0].value).toBe('B');
  });

  it('overwrites dirty modal state on a context refresh when editing was never set', async () => {
    const request = deferred<void>();
    const data = provider([{ key: 'title', value: 'Original' }]);
    editSettings.mockReturnValue(request.promise);
    const { result } = renderHook(() => group(), { wrapper: data.Wrapper });
    act(() => result.current.updateSetting('title', 'A'));
    let first!: Promise<boolean>;
    act(() => { first = result.current.handleSave(); });
    act(() => result.current.updateSetting('title', 'B'));
    expect(result.current.saveState).toBe('unsaved');
    act(() => data.refresh([{ key: 'title', value: 'A' }]));
    expect(result.current.localSettings[0]).toEqual({ key: 'title', value: 'A' });
    let returned!: boolean;
    await act(async () => { request.resolve(); returned = await first; });
    expect(returned).toBe(!head);
  });

  it('compares an unguarded second modal Save while the first is pending', async () => {
    const firstRequest = deferred<void>();
    const secondRequest = deferred<void>();
    const data = provider([{ key: 'title', value: 'Original' }]);
    let persisted = 'Original';
    editSettings.mockImplementation(async (changes: Setting[]) => {
      const value = changes[0].value;
      await (value === 'A' ? firstRequest.promise : secondRequest.promise);
      persisted = value;
    });
    const { result } = renderHook(() => group(), { wrapper: data.Wrapper });
    act(() => result.current.updateSetting('title', 'A'));
    let first!: Promise<boolean>;
    act(() => { first = result.current.handleSave(); });
    act(() => result.current.updateSetting('title', 'B'));
    expect(result.current.saveState).toBe('unsaved');
    let closed = false;
    // NavigationModal and Stripe Direct both await handleSave and then close
    // without consulting the returned boolean. This is their callback shape.
    const modalSave = async () => { await result.current.handleSave(); closed = true; };
    let second!: Promise<void>;
    await act(async () => { second = modalSave(); await Promise.resolve(); });
    expect(closed).toBe(head);
    expect(editSettings.mock.calls.map((call) => call[0][0].value)).toEqual(head ? ['A'] : ['A', 'B']);
    await act(async () => { firstRequest.resolve(); await first; });
    if (!head) {
      await act(async () => { secondRequest.resolve(); await second; });
    } else {
      await second;
    }
    expect(closed).toBe(true);
    expect(persisted).toBe(head ? 'A' : 'B');
  });

  it('shows the actual Design form replacing B with response A and retrying without a request', async () => {
    const request = deferred<{ settings: Setting[] }>();
    const data = provider([{ key: 'description', value: 'Original' }]);
    editSettings.mockReturnValue(request.promise);
    const { result } = renderHook(() => design(), { wrapper: data.Wrapper });
    act(() => result.current.updateGlobalSetting('description', 'A'));
    let first!: Promise<boolean>;
    act(() => { first = result.current.handleSave({ fakeWhenUnchanged: true }); });
    act(() => result.current.updateGlobalSetting('description', 'B'));
    expect(result.current.globalSettings.description).toBe('B');
    await act(async () => {
      request.resolve({ settings: [{ key: 'description', value: 'A' }] });
      await Promise.resolve();
      await vi.advanceTimersByTimeAsync(500);
    });
    expect(await first).toBe(!head);
    expect(result.current.globalSettings.description).toBe('A');
    expect(result.current.saveState).toBe(head ? 'unsaved' : 'saved');
    let retry!: Promise<boolean>;
    act(() => { retry = result.current.handleSave({ fakeWhenUnchanged: true }); });
    await act(async () => { await vi.advanceTimersByTimeAsync(500); });
    expect(await retry).toBe(true);
    expect(editSettings).toHaveBeenCalledTimes(1);
  });
});
