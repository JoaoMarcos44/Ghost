import React, { createContext, useContext } from 'react';

export type Setting = { key: string; value: string; dirty?: boolean };
export const GlobalContext = createContext<{ settings: Setting[] }>({ settings: [] });
export const useGlobalData = () => useContext(GlobalContext);
export const editSettings = vi.fn();
export const editThemeSettings = vi.fn();
export const setGlobalDirtyState = vi.fn();
export const useEditSettings = () => ({ mutateAsync: editSettings });
export const useEditCustomThemeSettings = () => ({ mutateAsync: editThemeSettings });
export const useBrowseCustomThemeSettings = () => ({ data: undefined });
export const useGlobalDirtyState = () => ({ setGlobalDirtyState });
export const getSettingValues = (settings: Setting[], keys: string[]) =>
  keys.map((key) => settings.find((setting) => setting.key === key)?.value);
