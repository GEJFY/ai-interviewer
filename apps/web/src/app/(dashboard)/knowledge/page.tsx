'use client';

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  Search,
  BookOpen,
  MessageSquare,
  Calendar,
  Tag,
  ChevronRight,
} from 'lucide-react';
import { format } from 'date-fns';
import { ja } from 'date-fns/locale';
import { apiClient } from '@/lib/api-client';
import { Button, Input } from '@/components/ui';

interface KnowledgeItem {
  id: string;
  title: string;
  content: string;
  source_type: string;
  source_interview_id: string | null;
  tags: string[];
  created_at: string;
  relevance_score?: number;
}

export default function KnowledgePage() {
  const [searchQuery, setSearchQuery] = useState('');
  const [isSearching, setIsSearching] = useState(false);

  const { data: searchResults, refetch } = useQuery({
    queryKey: ['knowledge-search', searchQuery],
    queryFn: async () => {
      if (!searchQuery.trim()) return null;
      const response = await apiClient.post('/knowledge/search', {
        query: searchQuery,
        limit: 20,
      });
      return response.data;
    },
    enabled: false,
  });

  const { data: recentItems, isLoading: isLoadingRecent } = useQuery({
    queryKey: ['knowledge-recent'],
    queryFn: async () => {
      const response = await apiClient.get('/knowledge', {
        params: { page: 1, pageSize: 10 },
      });
      return response.data;
    },
  });

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!searchQuery.trim()) return;
    setIsSearching(true);
    await refetch();
    setIsSearching(false);
  };

  const getSourceLabel = (type: string) => {
    switch (type) {
      case 'interview':
        return 'インタビュー';
      case 'document':
        return 'ドキュメント';
      case 'manual':
        return '手動入力';
      default:
        return type;
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-secondary-900">ナレッジ検索</h1>
        <p className="text-secondary-600 mt-1">
          過去のインタビューから蓄積されたナレッジを検索できます
        </p>
      </div>

      {/* Search */}
      <form onSubmit={handleSearch} className="flex gap-4">
        <div className="flex-1 relative">
          <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-secondary-400" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="キーワードや質問を入力して検索..."
            className="w-full pl-12 pr-4 py-3 border border-secondary-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
          />
        </div>
        <Button type="submit" isLoading={isSearching}>
          検索
        </Button>
      </form>

      {/* Search Results */}
      {searchResults?.items && searchResults.items.length > 0 && (
        <div className="bg-white rounded-xl border border-secondary-200">
          <div className="px-6 py-4 border-b border-secondary-200">
            <h2 className="font-semibold text-secondary-900">
              検索結果 ({searchResults.items.length}件)
            </h2>
          </div>
          <div className="divide-y divide-secondary-100">
            {searchResults.items.map((item: KnowledgeItem) => (
              <div key={item.id} className="px-6 py-4 hover:bg-secondary-50 transition">
                <div className="flex items-start gap-4">
                  <div className="p-2 bg-primary-100 rounded-lg">
                    <BookOpen className="w-5 h-5 text-primary-600" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <h3 className="font-medium text-secondary-900">{item.title}</h3>
                      {item.relevance_score && (
                        <span className="px-2 py-0.5 bg-green-100 text-green-700 text-xs rounded-full">
                          関連度 {Math.round(item.relevance_score * 100)}%
                        </span>
                      )}
                    </div>
                    <p className="text-sm text-secondary-600 line-clamp-2 mb-2">
                      {item.content}
                    </p>
                    <div className="flex items-center gap-4 text-xs text-secondary-500">
                      <span className="flex items-center gap-1">
                        <MessageSquare className="w-3 h-3" />
                        {getSourceLabel(item.source_type)}
                      </span>
                      <span className="flex items-center gap-1">
                        <Calendar className="w-3 h-3" />
                        {format(new Date(item.created_at), 'yyyy/MM/dd', { locale: ja })}
                      </span>
                      {item.tags.length > 0 && (
                        <span className="flex items-center gap-1">
                          <Tag className="w-3 h-3" />
                          {item.tags.slice(0, 3).join(', ')}
                        </span>
                      )}
                    </div>
                  </div>
                  <ChevronRight className="w-5 h-5 text-secondary-400" />
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* No Search Results */}
      {searchResults?.items && searchResults.items.length === 0 && (
        <div className="bg-white rounded-xl border border-secondary-200 p-12 text-center">
          <Search className="w-12 h-12 text-secondary-300 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-secondary-900 mb-2">
            検索結果がありません
          </h3>
          <p className="text-secondary-500">
            別のキーワードで検索してください
          </p>
        </div>
      )}

      {/* Recent Knowledge (when not searching) */}
      {!searchResults && (
        <div className="bg-white rounded-xl border border-secondary-200">
          <div className="px-6 py-4 border-b border-secondary-200">
            <h2 className="font-semibold text-secondary-900">最近のナレッジ</h2>
          </div>
          {isLoadingRecent ? (
            <div className="p-6">
              <div className="animate-pulse space-y-4">
                {[...Array(5)].map((_, i) => (
                  <div key={i} className="h-16 bg-secondary-100 rounded" />
                ))}
              </div>
            </div>
          ) : recentItems?.items?.length > 0 ? (
            <div className="divide-y divide-secondary-100">
              {recentItems.items.map((item: KnowledgeItem) => (
                <div key={item.id} className="px-6 py-4 hover:bg-secondary-50 transition">
                  <div className="flex items-start gap-4">
                    <div className="p-2 bg-secondary-100 rounded-lg">
                      <BookOpen className="w-5 h-5 text-secondary-600" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <h3 className="font-medium text-secondary-900 mb-1">{item.title}</h3>
                      <p className="text-sm text-secondary-600 line-clamp-2 mb-2">
                        {item.content}
                      </p>
                      <div className="flex items-center gap-4 text-xs text-secondary-500">
                        <span className="flex items-center gap-1">
                          <MessageSquare className="w-3 h-3" />
                          {getSourceLabel(item.source_type)}
                        </span>
                        <span className="flex items-center gap-1">
                          <Calendar className="w-3 h-3" />
                          {format(new Date(item.created_at), 'yyyy/MM/dd', { locale: ja })}
                        </span>
                        {item.tags.length > 0 && (
                          <span className="flex items-center gap-1">
                            <Tag className="w-3 h-3" />
                            {item.tags.slice(0, 3).join(', ')}
                          </span>
                        )}
                      </div>
                    </div>
                    <ChevronRight className="w-5 h-5 text-secondary-400" />
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="p-12 text-center">
              <BookOpen className="w-12 h-12 text-secondary-300 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-secondary-900 mb-2">
                ナレッジがありません
              </h3>
              <p className="text-secondary-500">
                インタビュー完了後、自動的にナレッジが抽出されます
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
